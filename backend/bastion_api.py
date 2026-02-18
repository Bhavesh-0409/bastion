from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime
import json
import os
import uuid
from typing import Dict, List, Any
from pathlib import Path

# Import modules from sibling packages
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ml.classifier import MLClassifier
from rules.rule_engine import RuleEngine

app = FastAPI(title="Bastion Security Layer")

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
# SIMPLE SESSION STATE MANAGER (in-memory)
# ============================================================================
class SessionStateManager:
    """Minimal session state manager for tracking analysis sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, metadata: Dict = None) -> str:
        """Create new session and return session_id"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "id": session_id,
            "created_at": datetime.now().isoformat(),
            "analyses": [],
            "metadata": metadata or {}
        }
        return session_id
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Retrieve session by ID"""
        return self.sessions.get(session_id)
    
    def add_analysis(self, session_id: str, analysis_result: Dict) -> None:
        """Add analysis result to session"""
        if session_id in self.sessions:
            self.sessions[session_id]["analyses"].append(analysis_result)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions"""
        return list(self.sessions.values())


# ============================================================================
# SIMPLE AUDIT LOGGER (writes to logs/ folder)
# ============================================================================
class AuditLogger:
    """Minimal audit logger for security events"""
    
    def __init__(self, logs_dir: str = "../logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.logs_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
    
    def log_analysis(self, session_id: str, prompt: str, result: Dict) -> None:
        """Log analysis event to audit log"""
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
        """Retrieve recent audit logs"""
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
    """Orchestrates the security analysis execution pipeline"""
    
    def __init__(self):
        self.classifier = MLClassifier()
        self.rule_engine = RuleEngine()
        self.session_manager = SessionStateManager()
        self.audit_logger = AuditLogger()
    
    def execute(self, prompt: str, bastion_enabled: bool = True) -> Dict[str, Any]:
        """
        Execute complete analysis pipeline.
        
        Pipeline:
        1. Call ml.classifier.evaluate(prompt)
        2. Call rules.rule_engine.decide(risk_result, bastion_enabled)
        3. Aggregate results into structured response
        """
        
        # Step 1: ML Classification
        _, risk_score = self.classifier.predict(prompt)
        
        # Step 2: Rules Engine
        is_safe, violations = self.rule_engine.check_prompt(prompt)
        
        # Step 3: Decision Logic
        violation_types = list(set([v.get("rule_name", "unknown") for v in violations]))
        violation_type = violation_types[0] if violation_types else "none"
        confidence = 0.95 if violations else 0.85
        
        # Determine decision based on risk and bastion setting
        if not bastion_enabled:
            decision = "allow"
        elif risk_score > 0.7 or violations:
            decision = "block"
        else:
            decision = "allow"
        
        # Step 4: Aggregated Response
        result = {
            "risk_score": round(risk_score, 2),
            "violation_type": violation_type,
            "confidence": round(confidence, 2),
            "decision": decision,
            "integrity_score": round(1.0 - risk_score, 2),
            "instruction_depth": len([v for v in violations if v.get("severity") == "high"]),
            "violations": violations,
            "timestamp": datetime.now().isoformat()
        }
        
        return result


# Initialize pipeline
pipeline = AnalysisPipeline()


# ============================================================================
# REQUEST/RESPONSE MODELS
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

class PromptRequest(BaseModel):
    prompt: str
    model: str = "default"

class SecurityResponse(BaseModel):
    safe: bool
    threat_level: str
    details: dict
    timestamp: str


# ============================================================================
# ENDPOINTS
# ============================================================================
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Main security analysis endpoint following clean execution pipeline.
    
    Executes:
    1. ML classifier evaluation
    2. Rules engine decision logic
    3. Returns structured security assessment
    """
    try:
        # Create session for this analysis
        session_id = pipeline.session_manager.create_session({
            "model": request.model
        })
        
        # Execute analysis pipeline
        result = pipeline.execute(request.prompt, request.bastion_enabled)
        
        # Log to audit
        pipeline.audit_logger.log_analysis(session_id, request.prompt, result)
        
        # Add to session
        pipeline.session_manager.add_analysis(session_id, result)
        
        # Add session_id to response
        result["session_id"] = session_id
        
        return AnalyzeResponse(**result)
        
    except Exception as e:
        logger.error(f"Analysis pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/prompt/check")
async def check_prompt(request: PromptRequest) -> SecurityResponse:
    """Legacy endpoint - Check prompt for security threats"""
    try:
        result = pipeline.execute(request.prompt)
        threat_level = "blocked" if result["decision"] == "block" else "safe"
        
        return SecurityResponse(
            safe=result["decision"] == "allow",
            threat_level=threat_level,
            details={
                "risk_score": result["risk_score"],
                "violations": result["violations"]
            },
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Prompt check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs")
async def get_logs(limit: int = 100):
    """Retrieve recent security audit logs"""
    logs = pipeline.audit_logger.get_recent_logs(limit)
    return {"logs": logs, "total": len(logs)}

@app.get("/sessions")
async def list_sessions():
    """List all active analysis sessions"""
    sessions = pipeline.session_manager.list_sessions()
    return {"sessions": sessions, "total": len(sessions)}

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Retrieve specific session details"""
    session = pipeline.session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
