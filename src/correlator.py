import json
from typing import List, Tuple
from src.schemas import Alert, IncidentCluster

with open("data/topology.json", "r", encoding="utf-8") as f:
    TOPOLOGY = json.load(f)["nodes"]

def get_all_descendants(node: str) -> List[str]:
    """Recursively fetch all child and descendant nodes."""
    descendants = []
    children = TOPOLOGY.get(node, {}).get("children", [])
    for child in children:
        descendants.append(child)
        descendants.extend(get_all_descendants(child))
    return list(set(descendants))

def correlate_alerts(alerts: List[Alert]) -> Tuple[List[IncidentCluster], List[Alert]]:
    clusters = []
    noise = []
    device_alerts = {}
    for a in alerts:
        device_alerts.setdefault(a.device, []).append(a)

    processed_ids = set()

    # Sort topology by tier hierarchy (core first, then aggregation, then access)
    tier_order = {"core": 0, "aggregation": 1, "gateway": 2, "access": 3}
    sorted_nodes = sorted(TOPOLOGY.keys(), key=lambda k: tier_order.get(TOPOLOGY[k].get("tier"), 9))

    for node in sorted_nodes:
        if node in device_alerts:
            # Check if any alert on this node wasn't already absorbed by an upstream node
            node_unprocessed = [a for a in device_alerts[node] if a.id not in processed_ids]
            if not node_unprocessed:
                continue

            descendants = get_all_descendants(node)
            related_alerts = list(node_unprocessed)
            affected = [node]

            for desc in descendants:
                if desc in device_alerts:
                    for a in device_alerts[desc]:
                        if a.id not in processed_ids:
                            related_alerts.append(a)
                            affected.append(desc)

            # If it's a core node or has multiple cascading failures, group it
            if len(related_alerts) > 1 or any(a.severity == "CRITICAL" for a in related_alerts):
                cluster_id = f"INC-{node}-{related_alerts[0].id}"
                clusters.append(IncidentCluster(
                    incident_id=cluster_id,
                    primary_device=node,
                    affected_devices=list(set(affected)),
                    alert_ids=[a.id for a in related_alerts],
                    alert_codes=list(set(a.code for a in related_alerts)),
                    root_cause_hypothesis=f"Upstream link or transport failure on {node}",
                    severity="P1" if any(a.severity == "CRITICAL" for a in related_alerts) else "P2"
                ))
                for a in related_alerts:
                    processed_ids.add(a.id)

    # Secondary: Group remaining localized multi-alerts on single devices
    for dev, dev_alist in device_alerts.items():
        unhandled = [a for a in dev_alist if a.id not in processed_ids]
        if len(unhandled) >= 2:
            cluster_id = f"INC-{dev}-{unhandled[0].id}"
            clusters.append(IncidentCluster(
                incident_id=cluster_id,
                primary_device=dev,
                affected_devices=[dev],
                alert_ids=[a.id for a in unhandled],
                alert_codes=[a.code for a in unhandled],
                root_cause_hypothesis=f"Localized degradation on {dev}",
                severity="P2" if any(a.severity in ["HIGH", "CRITICAL"] for a in unhandled) else "P3"
            ))
            for a in unhandled:
                processed_ids.add(a.id)

    # Isolated alerts without correlation remain as noise
    for a in alerts:
        if a.id not in processed_ids:
            noise.append(a)

    return clusters, noise