from pydantic import BaseModel
from typing import List, Optional

class Alert(BaseModel):
    id: str
    timestamp: str
    device: str
    code: str
    severity: str
    message: str

class IncidentCluster(BaseModel):
    incident_id: str
    primary_device: str
    affected_devices: List[str]
    alert_ids: List[str]
    alert_codes: List[str]
    root_cause_hypothesis: str
    severity: str

class TriageResult(BaseModel):
    incident_id: str
    status: str
    severity: str
    matched_runbook_id: Optional[str] = None
    cited_sections: List[str] = []
    recommended_action: str
    escalation_reason: Optional[str] = None
    evidence_summary: str