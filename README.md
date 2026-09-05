TRACK_ID=PS07

# Autonomous Telecom Network Incident Triage Assistant

An intelligent NOC assistant that deterministically ingests raw alert streams, deduplicates and clusters correlated failures by topology, matches runbooks via local embeddings, and grounds initial remediation steps or generates structured escalation dossiers.

## System Design & Workflow
1. **Deterministic Correlation:** Ingests raw telemetry and uses network topology (Core -> Aggregation -> Access) to collapse cascading outages into single root incidents while isolating unassociated events as noise.
2. **Local Vector Retrieval:** Runbooks are indexed locally using FAISS and cosine similarity via text embeddings. High-confidence matches (>0.65 threshold) are passed to the triage agent; unmatched failures are flagged for escalation.
3. **Grounded AI Triage:** Gemini 2.5 Flash acts strictly on runbook evidence, citing explicit steps for remediation. When an incident is zero-day or uncovered, it builds an engineering escalation dossier without hallucinating procedures.

## Quick Start
```bash
pip install -r requirements.txt
export GEMINI_API_KEY="your-api-key"
python app.py