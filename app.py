import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from src.schemas import Alert
from src.correlator import correlate_alerts
from src.triage_engine import triage_incident

app = FastAPI(title="Telecom NOC Incident Triage")

with open("data/scenarios.json", "r") as f:
    SCENARIOS = json.load(f)

@app.post("/api/triage/{scenario_key}")
async def trigger_triage(scenario_key: str):
    if scenario_key not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    raw_alerts = [Alert(**item) for item in SCENARIOS[scenario_key]["alerts"]]
    clusters, noise = correlate_alerts(raw_alerts)
    
    triage_results = [triage_incident(c) for c in clusters]
        
    return {
        "scenario": SCENARIOS[scenario_key]["name"],
        "noise": [n.model_dump() for n in noise],
        "clusters": [c.model_dump() for c in clusters],
        "triage_results": [r.model_dump() for r in triage_results]
    }

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False) 