"""FastAPI endpoints for Solar Agent REST API."""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Body, Request
from fastapi.responses import JSONResponse
from solar_agent.core.config import settings
from solar_agent.core.models import (
    AgentMode,
    CurtailmentCommand,
    CurtailmentStatus,
)
from solar_agent.api.models import (
    CurtailmentRequest,
    StatusResponse,
    HealthResponse,
)
import asyncio
import random
from pydantic import BaseModel
from solar_agent.tools.data_generator import DeviceStateManager
from fastapi import status
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from solar_agent.workflow.graph import WorkflowManager
from solar_agent.workflow.state import WorkflowState
from solar_agent.adapters import get_adapter


logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# --- Configurable Device IDs ---
DEVICE_IDS = [f"agent_{i+1}" for i in range(5)]

# --- Dependency Provider ---
def get_device_manager():
    # In production, this could be a singleton or injected via FastAPI's startup event
    if not hasattr(get_device_manager, "manager"):
        get_device_manager.manager = DeviceStateManager(DEVICE_IDS)
    return get_device_manager.manager

# --- Pydantic Models ---
class CurtailmentRequest(BaseModel):
    amount: float

class LLMRequest(BaseModel):
    input: str
    provider: Optional[str] = None
    model: Optional[str] = None

# --- API Endpoints ---

@router.on_event("startup")
async def start_periodic_logging():
    manager = get_device_manager()
    asyncio.create_task(manager.periodic_logging())

@router.get("/devices", response_model=List[str])
async def get_devices(manager: DeviceStateManager = Depends(get_device_manager)):
    return await manager.get_devices()

@router.get("/status", response_model=List[Dict[str, Any]])
async def get_all_status(manager: DeviceStateManager = Depends(get_device_manager)):
    return await manager.get_all_status()

@router.get("/status/{agent_id}", response_model=Dict[str, Any])
async def get_status_by_id(agent_id: str, manager: DeviceStateManager = Depends(get_device_manager)):
    state = await manager.get_status(agent_id)
    if not state:
        raise HTTPException(status_code=404, detail="Agent not found")
    return state

@router.post("/curtailment")
async def curtailment(req: CurtailmentRequest):
    agent_id = settings.AGENT_ID
    state = await workflow_manager.get_state(agent_id)
    if not state:
        state = WorkflowState(agent_id=agent_id)
    state.active_curtailment = req.amount
    await workflow_manager.update_state(agent_id, {"active_curtailment": req.amount})
    return {"message": f"Curtailment applied: {req.amount} kW"}

@router.get("/logs")
async def get_all_logs(manager: DeviceStateManager = Depends(get_device_manager)):
    return await manager.get_logs()

@router.get("/logs/{agent_id}")
async def get_logs_by_id(agent_id: str, manager: DeviceStateManager = Depends(get_device_manager)):
    logs = await manager.get_logs(agent_id)
    if logs is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return logs

@router.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "status": "running",
        "agent_id": settings.agent_id,
    }

@router.get("/capabilities")
async def get_capabilities():
    """Return agent capabilities for ecosystem discovery (JSON-LD style)."""
    return {
        "@context": "https://schema.org/",
        "@type": "SolarAgentCapabilities",
        "agent_id": "solar-agent-standalone",
        "supported_hardware": ["MockAdapter", "SunSpecAdapter"],
        "llm_providers": ["openai", "gemini", "ollama"],
        "control_modes": ["curtailment", "forecasting", "status", "maintenance"],
        "endpoints": {
            "status": "/status/{agent_id}",
            "curtailment": "/curtailment",
            "logs": "/logs/{agent_id}",
            "devices": "/devices",
        },
        "integration": {
            "standalone": True,
            "ecosystem_ready": True,
            "description": "Can operate independently or as part of a multi-agent grid with utility, battery, and load agents."
        },
        "version": "1.0.0"
    }

@router.get("/status")
async def get_status():
    agent_id = settings.AGENT_ID
    state = await workflow_manager.get_state(agent_id)
    if not state:
        raise HTTPException(status_code=404, detail="Agent state not found")
    return {
        "generation_kw": getattr(state.latest_solar_data, 'generation_kw', 0),
        "forecast_kw": state.current_forecast or 0,
        "mode": state.current_mode,
        "alerts": [f.description for f in state.active_faults] if state.active_faults else [],
    }

@router.get("/alerts")
async def get_alerts():
    agent_id = settings.AGENT_ID
    state = await workflow_manager.get_state(agent_id)
    if not state:
        return {"alerts": []}
    return {"alerts": [f.description for f in state.active_faults] if state.active_faults else []}

@router.get("/health")
async def health():
    return {"status": "ok"}

@router.get("/metrics")
async def metrics():
    agent_id = settings.AGENT_ID
    state = await workflow_manager.get_state(agent_id)
    if not state:
        return {"generation_kw": 0, "forecast_kw": 0, "mode": "unknown", "alerts_count": 0}
    return {
        "generation_kw": getattr(state.latest_solar_data, 'generation_kw', 0),
        "forecast_kw": state.current_forecast or 0,
        "mode": state.current_mode,
        "alerts_count": len(state.active_faults) if state.active_faults else 0
    }

@router.post("/explain")
async def explain_endpoint(req: LLMRequest):
    from solar_agent.workflow.nodes import explain_action
    agent_id = settings.AGENT_ID
    state = await workflow_manager.get_state(agent_id)
    return await explain_action(req.input, provider=req.provider, model=req.model, state=state)

@router.post("/negotiate")
async def negotiate_endpoint(req: LLMRequest):
    from solar_agent.workflow.nodes import negotiate_action
    agent_id = settings.AGENT_ID
    state = await workflow_manager.get_state(agent_id)
    return await negotiate_action(req.input, provider=req.provider, model=req.model, state=state)

@router.post("/interpret")
async def interpret_endpoint(req: LLMRequest):
    from solar_agent.workflow.nodes import interpret_instruction
    agent_id = settings.AGENT_ID
    state = await workflow_manager.get_state(agent_id)
    return await interpret_instruction(req.input, provider=req.provider, model=req.model, state=state)

@router.post("/ask")
async def ask_endpoint(req: LLMRequest):
    from solar_agent.workflow.nodes import answer_question
    agent_id = settings.AGENT_ID
    state = await workflow_manager.get_state(agent_id)
    return await answer_question(req.input, provider=req.provider, model=req.model, state=state)

@router.get("/llm-usage")
async def llm_usage_endpoint():
    # Placeholder: will return LLM usage logs
    return {"usage": []}

# Shared workflow manager (singleton for now)
adapter = get_adapter()
workflow_manager = WorkflowManager(adapter) 