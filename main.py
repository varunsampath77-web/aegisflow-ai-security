
from fastapi import FastAPI
from pydantic import BaseModel, Field

from security import evaluate_request
from audit import log_event, get_logs, verify_chain

app = FastAPI(
    title="AgentGuard",
    description="Least-Privilege Permission Firewall for AI Agents",
    version="1.0.0"
)


class ToolRequest(BaseModel):
    agent: str = Field(min_length=1, max_length=100)
    action: str = Field(min_length=1, max_length=100)
    content: str = Field(default="", max_length=10000)


@app.get("/")
def home():
    return {
        "project": "AgentGuard",
        "status": "running",
        "message": "AI Agent Security Firewall"
    }


@app.post("/tool-call")
def tool_call(request: ToolRequest):
    result = evaluate_request(
        request.agent,
        request.action,
        request.content
    )

    # This MVP simulates execution; it does not run real tools.
    executed = result["decision"] == "ALLOW"

    log_event(
        request.agent,
        request.action,
        result["decision"],
        result["risk_score"],
        result["reason"]
    )

    return {
        "agent": request.agent,
        "action": request.action,
        "decision": result["decision"],
        "risk_score": result["risk_score"],
        "reason": result["reason"],
        "simulated_execution": executed
    }


@app.get("/logs")
def logs():
    return get_logs()


@app.get("/verify")
def verify():
    return {
        "chain_valid": verify_chain()
    }
