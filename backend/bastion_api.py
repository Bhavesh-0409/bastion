from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime

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

# Models
class PromptRequest(BaseModel):
    prompt: str
    model: str = "default"

class SecurityResponse(BaseModel):
    safe: bool
    threat_level: str  # "safe", "warning", "blocked"
    details: dict
    timestamp: str

# Endpoints
@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/prompt/check")
async def check_prompt(request: PromptRequest) -> SecurityResponse:
    """Check prompt for security threats"""
    logger.info(f"Checking prompt for model: {request.model}")
    
    # TODO: Integrate rule_engine and ml classifier
    # For now, placeholder logic
    return SecurityResponse(
        safe=True,
        threat_level="safe",
        details={"rules_checked": 0, "ml_score": 0.0},
        timestamp=datetime.now().isoformat()
    )

@app.get("/logs")
async def get_logs(limit: int = 100):
    """Retrieve recent security logs"""
    # TODO: Read from logs directory
    return {"logs": [], "total": 0}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
