# RB-002: AAA/RADIUS Authentication Storm & Gateway Saturation
**Category:** Subscriber Management & Access Control
**Triggers:** Repeated RADIUS Access-Reject spikes (>500/sec), High CPU on BNG (Broadband Network Gateway), Latency spikes on subscriber auth.

## 1. Initial Assessment
- Check AAA server cluster health and packet drop rates on port 1812/1813.
- Verify if recent firmware update or expired SSL certificate triggered client reconnect storms.

## 2. Mitigation Steps
- **Step 2.1:** Apply rate-limiting policy on ingress auth packets: `access-control-list AAA-POLICING rate-limit 2000 pps`.
- **Step 2.2:** Failover subscriber authentication traffic to secondary standby RADIUS cluster.
- **Step 2.3:** Clear stale session queues on affected edge aggregation nodes.