from backend.audit_logger import init_db, get_logs as get_session_logs
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime
import json
import os
import uuid
import sqlite3

from typing import Dict, List, Any
from pathlib import Path
from backend.audit_logger import insert_log

# Import modules from sibling packages
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ml.classifier import evaluate

from rules.rule_engine import RuleEngine

app = FastAPI(title="Bastion Security Layer")



# Initialize DB on startup
init_db()

# CORS for Streamlit UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# SESSION STATE MANAGER
# ============================================================================
class SessionStateManager:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, metadata: Dict = None) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "id": session_id,
            "created_at": datetime.now().isoformat(),
            "analyses": [],
            "metadata": metadata or {}
        }
        return session_id

    def get_session(self, session_id: str) -> Dict[str, Any]:
        return self.sessions.get(session_id)

    def add_analysis(self, session_id: str, analysis_result: Dict) -> None:
        if session_id in self.sessions:
            self.sessions[session_id]["analyses"].append(analysis_result)

    def list_sessions(self) -> List[Dict[str, Any]]:
        return list(self.sessions.values())

# ============================================================================
# SIMPLE FILE AUDIT LOGGER (legacy JSONL)
# ============================================================================
class AuditLogger:
    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.logs_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"

    def log_analysis(self, session_id: str, prompt: str, result: Dict) -> None:
        event = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "prompt_length": len(prompt),
            "risk_score": result.get("risk_score"),
            "decision": result.get("decision"),
            "violation_count": len(result.get("violations", []))
        }

        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def get_recent_logs(self, limit: int = 100) -> List[Dict]:
        logs = []
        try:
            with open(self.log_file, "r") as f:
                for line in f.readlines()[-limit:]:
                    if line.strip():
                        logs.append(json.loads(line))
        except FileNotFoundError:
            pass
        return logs


# ============================================================================
# EXECUTION PIPELINE
# ============================================================================
class AnalysisPipeline:
    def __init__(self):
        self.rule_engine = RuleEngine()
        self.session_manager = SessionStateManager()
        self.audit_logger = AuditLogger()

    def execute(self, prompt: str, bastion_enabled: bool = True) -> Dict[str, Any]:

        # ML Evaluation
        ml_result = evaluate(prompt)
        ml_risk = ml_result["risk_score"]
        violation_type = ml_result["violation_type"]
        confidence = ml_result["confidence"]

        # Rule Engine
        is_safe, violations = self.rule_engine.check_prompt(prompt)
        
        # DEBUG: Log RuleEngine execution
        logger.info(f"[DEBUG] RuleEngine - Total rules loaded: {len(self.rule_engine.rules)}")
        logger.info(f"[DEBUG] RuleEngine - Violations triggered: {len(violations)}")
        if violations:
            triggered_rule_ids = [v.get("rule_id") for v in violations]
            logger.info(f"[DEBUG] RuleEngine - Triggered rule IDs: {triggered_rule_ids}")

        # Calculate Rule Risk with severity weights
        severity_weights = {
            "low": 0.1,
            "medium": 0.3,
            "high": 0.6
        }
        rule_risk = sum(severity_weights.get(v.get("severity", "low"), 0.1) for v in violations)
        rule_risk = min(rule_risk, 1.0)  # Cap at 1.0

        # Check for explicit safety violations (suicide, violence, harm)
        safety_violation_intents = {
            "SuicideIdeation", "SelfHarmIntent", "ViolenceThreat", 
            "PhysicalThreat", "HarmEncouragement", "WeaponUseIntent", "CoercionThreat"
        }
        high_severity_safety_violations = [
            v for v in violations 
            if v.get("severity") == "high" and v.get("intent") in safety_violation_intents
        ]

        # Weighted Composite Risk Formula
        final_risk = (0.6 * ml_risk) + (0.4 * rule_risk)

        # If there are explicit safety violations, boost the risk significantly
        if high_severity_safety_violations:
            final_risk = max(final_risk, 0.85)  # Ensure at least 0.85 for explicit safety threats
            logger.warning(f"[DEBUG] SAFETY VIOLATION DETECTED - Boosting risk to {final_risk}")

        # Confidence Adjustment
        final_risk += (1 - confidence) * 0.1

        # Cap final_risk at 1.0
        final_risk = min(final_risk, 1.0)

        # Decision Logic
        if not bastion_enabled:
            decision = "allow"
        elif final_risk >= 0.8:
            decision = "block"
        elif final_risk >= 0.5:
            decision = "review"
        else:
            decision = "allow"

        result = {
            "risk_score": round(final_risk, 2),
            "violation_type": violation_type,
            "confidence": round(confidence, 2),
            "decision": decision,
            "integrity_score": round(1.0 - final_risk, 2),
            "instruction_depth": len(
                [v for v in violations if v.get("severity") == "high"]
            ),
            "violations": violations,
            "timestamp": datetime.now().isoformat()
        }

        return result


pipeline = AnalysisPipeline()


# ============================================================================
# MODELS
# ============================================================================
class AnalyzeRequest(BaseModel):
    prompt: str
    bastion_enabled: bool = True
    model: str = "default"


class AnalyzeResponse(BaseModel):
    risk_score: float
    violation_type: str
    confidence: float
    decision: str
    integrity_score: float
    instruction_depth: int
    violations: List[Dict]
    timestamp: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    try:
        session_id = pipeline.session_manager.create_session({
            "model": request.model
        })

        result = pipeline.execute(request.prompt, request.bastion_enabled)

        # JSONL log
        pipeline.audit_logger.log_analysis(session_id, request.prompt, result)

        # SQLite log (REAL persistence)
        insert_log(
            session_id=session_id,
            risk_score=result["risk_score"],
            violation_type=result["violation_type"],
            decision=result["decision"],
            integrity_score=result["integrity_score"],
            instruction_depth=result["instruction_depth"],
            violations=len(result["violations"])
        )

        pipeline.session_manager.add_analysis(session_id, result)

        return AnalyzeResponse(**result)

    except Exception as e:
        logger.error(f"Analysis pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 🔹 IMPORTANT: Static route FIRST
@app.get("/logs/recent")
async def get_recent_logs(limit: int = 100):
    conn = sqlite3.connect("data/bastion.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT timestamp, risk_score, decision, integrity_score
        FROM audit_logs
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return {
        "logs": [
            {
                "timestamp": row[0],
                "risk_score": row[1],
                "decision": row[2],
                "integrity_score": row[3]
            }
            for row in rows
        ],
        "total": len(rows)
    }


# 🔹 Dynamic route AFTER
@app.get("/logs/{session_id}")
def fetch_logs(session_id: str):
    return get_session_logs(session_id)


@app.get("/sessions")
async def list_sessions():
    sessions = pipeline.session_manager.list_sessions()
    return {"sessions": sessions, "total": len(sessions)}


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    session = pipeline.session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
