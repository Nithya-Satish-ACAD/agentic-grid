from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import logging
from ..adapters.eventbus import EventBus
from .models import (
    UtilityState as StateResponse,
    CurtailmentRequest,
    RegisterDERRequest,
    BecknMessage,
    DERAgent,
    Conflict,
)
from ..beckn.stubs import stub_on_search, stub_confirm, stub_on_confirm

router = APIRouter()

logger = logging.getLogger(__name__)

# Global state (for simplicity; use persistence in production)
state = StateResponse()
event_bus = EventBus()

@router.get("/status", response_model=StateResponse)
async def get_status():
    return state

@router.post("/curtailment")
async def issue_curtailment(request: CurtailmentRequest):
    if request.agent_id not in [der.id for der in state.registered_ders]:
        raise HTTPException(status_code=404, detail="DER not registered")
    # Publish to event bus
    try:
        await event_bus.connect()
        await event_bus.publish("utility.curtailment", request)
        state.flexibility_plans.append(  # Simplified
            FlexibilityPlan(
                agent_id=request.agent_id,
                amount=request.amount,
                duration=request.duration,
                start_time=datetime.datetime.utcnow(),
            )
        )
        return {"status": "curtailment issued"}
    except Exception as e:
        logger.error(f"Curtailment error: {e}")
        raise HTTPException(status_code=500, detail="Failed to issue curtailment")

@router.get("/alerts", response_model=List[str])
async def get_alerts():
    return state.alerts

@router.post("/register_der")
async def register_der(request: RegisterDERRequest):
    if request.type not in ["solar", "battery", "load"]:
        raise HTTPException(status_code=400, detail="Unsupported DER type")
    new_der = DERAgent(id=request.id, type=request.type, ip_address=request.ip_address, status="online")
    state.registered_ders.append(new_der)
    return {"status": "DER registered", "der_id": request.id}

@router.get("/conflicts", response_model=List[Conflict])
async def get_conflicts():
    return state.conflicts

# Beckn Stub Endpoints
@router.post("/beckn/on_search")
async def beckn_on_search(payload: Dict[str, Any]):
    return stub_on_search(payload)

@router.post("/beckn/confirm")
async def beckn_confirm(payload: Dict[str, Any]):
    return stub_confirm(payload)

@router.post("/beckn/on_confirm")
async def beckn_on_confirm(payload: Dict[str, Any]):
    return stub_on_confirm(payload)

# Add more Beckn stubs as needed

# To integrate new agents dynamically:
# 1. Register via /register_der endpoint.
# 2. Subscribe to their status topics in eventbus.
# 3. Extend workflow nodes to handle new types (e.g., specific curtailment logic).
