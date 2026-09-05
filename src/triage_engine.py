import os
import json
from google import genai
from google.genai import types
from src.schemas import IncidentCluster, TriageResult
from src.retriever import LocalRunbookStore

retriever = LocalRunbookStore()

def _call_gemini_json(client: genai.Client, prompt: str) -> dict:
    """Invokes Gemini with standard fallbacks across supported API models."""
    candidate_models = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-1.5-flash"]
    last_err = None

    for model_name in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0
                )
            )
            return json.loads(response.text)
        except Exception as e:
            last_err = e
            continue

    raise RuntimeError(f"All candidate Gemini models failed: {last_err}")

def triage_incident(incident: IncidentCluster) -> TriageResult:
    query = f"Incident on {incident.primary_device}. Codes: {', '.join(incident.alert_codes)}. Hypothesis: {incident.root_cause_hypothesis}"
    matched = retriever.search(query)
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    if matched:
        prompt = f"""
You are a Network Operations Center triage AI. Recommend initial triage actions strictly grounded in the provided runbook excerpt.
Do NOT invent procedures.

Runbook ID: {matched['runbook_id']}
Runbook Excerpt:
{matched['text']}

Incident Details:
- Primary Device: {incident.primary_device}
- Affected Nodes: {incident.affected_devices}
- Alerts: {incident.alert_codes}

Return JSON with these exact keys:
{{
  "cited_sections": ["list of section numbers or titles cited directly"],
  "recommended_action": "clear operational step directly quoting or referencing the runbook",
  "evidence_summary": "why this runbook applies"
}}
"""
        data = _call_gemini_json(client, prompt)
        return TriageResult(
            incident_id=incident.incident_id,
            status="RESOLVED_BY_RUNBOOK",
            severity=incident.severity,
            matched_runbook_id=matched["runbook_id"],
            cited_sections=data.get("cited_sections", []),
            recommended_action=data.get("recommended_action", ""),
            evidence_summary=data.get("evidence_summary", "")
        )
    else:
        prompt = f"""
You are an expert telecom triage system. No runbook exists for this incident.
Assemble a disciplined technical escalation handover context for Tier 3 network engineering.
State clearly what is known, what failed, and why it cannot be resolved automatically.

Incident:
- Primary Device: {incident.primary_device}
- Affected Nodes: {incident.affected_devices}
- Alert Codes: {incident.alert_codes}
- Hypothesis: {incident.root_cause_hypothesis}

Return JSON with these exact keys:
{{
  "escalation_reason": "explicit statement of why this requires manual specialist handover",
  "recommended_action": "recommended containment or safe inspection action for Tier 3",
  "evidence_summary": "blast radius and grouped signals summary"
}}
"""
        data = _call_gemini_json(client, prompt)
        return TriageResult(
            incident_id=incident.incident_id,
            status="ESCALATED",
            severity=incident.severity,
            escalation_reason=data.get("escalation_reason", "No matching runbook found in local repository"),
            recommended_action=data.get("recommended_action", "Engage Tier 3 Engineering"),
            evidence_summary=data.get("evidence_summary", "")
        )