"""
FastAPI endpoints for the Utility Agent.
"""
import logging
import uuid
from fastapi import APIRouter, HTTPException, Request, Depends

from .models import (
    AckPayload,
    RegisterDERPayload,
    HeartbeatPayload,
    CurtailmentCommand,
    UtilityState,
    SimpleAck,
    BecknSearchRequest,
    BecknResponse,
    BackgroundServices,
)
from ..workflow.state import get_services
# The workflow and state are no longer globals, they will be injected via requests.

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()

# ==============================================================================
#  PUBLIC API ENDPOINTS
# ==============================================================================

@router.get("/status", response_model=UtilityState)
async def get_status(request: Request):
    """Returns the current state of the utility agent."""
    return request.app.state.workflow.state

@router.post("/register_der", status_code=200, response_model=SimpleAck)
async def register_der(payload: RegisterDERPayload, request: Request):
    """Endpoint for a new DER to register with the utility."""
    logger.info(f"API: Received registration for {payload.id}")
    workflow = request.app.state.workflow
    await workflow.register_der(payload)
    return SimpleAck(status="success") # Changed from "ok" to "success"

@router.post("/heartbeat", status_code=200, response_model=SimpleAck)
async def heartbeat(payload: HeartbeatPayload, request: Request):
    """Endpoint for a DER to send a heartbeat."""
    logger.debug(f"API: Received heartbeat from {payload.id}")
    workflow = request.app.state.workflow
    await workflow.process_heartbeat(payload)
    return SimpleAck(status="ok")

@router.post("/ack", status_code=200, response_model=SimpleAck)
async def ack(payload: AckPayload, request: Request):
    """Endpoint for a DER to send an acknowledgement for a command."""
    logger.info(f"API: Received ACK for command {payload.command_id} from {payload.agent_id} with status: {payload.status}")
    # Here you could add logic to update the command's state in the workflow
    # For now, we just log it and acknowledge receipt.
    return SimpleAck(status="acknowledged")


@router.post("/commands/curtail", status_code=200, response_model=AckPayload)
async def curtail_der(command: CurtailmentCommand, request: Request):
    """Endpoint for receiving a curtailment command (for compliance)."""
    logger.info(f"API: Received curtailment command for {command.agent_id}")
    # In a real scenario, this would trigger a workflow to handle the command
    request.app.state.workflow.state.active_commands[command.agent_id] = command
    return AckPayload(status="ok")

# ==============================================================================
#  BECKN / UEI STUB ENDPOINTS
# ==============================================================================

@router.post("/beckn/on_search", tags=["Beckn Stubs"])
async def on_search(payload: dict):
    # UEI-GridOn/1.0.0/on_search
    logger.info(f"BECKN STUB: Received on_search: {payload}")
    return {"message": {"ack": {"status": "ACK"}}}

@router.post("/beckn/on_select", tags=["Beckn Stubs"])
async def on_select(payload: dict):
    # UEI-GridOn/1.0.0/on_select
    logger.info(f"BECKN STUB: Received on_select: {payload}")
    return {"message": {"ack": {"status": "ACK"}}}

@router.post("/beckn/on_init", tags=["Beckn Stubs"])
async def on_init(payload: dict):
    # UEI-GridOn/1.0.0/on_init
    logger.info(f"BECKN STUB: Received on_init: {payload}")
    return {"message": {"ack": {"status": "ACK"}}}

@router.post("/beckn/on_confirm", tags=["Beckn Stubs"])
async def on_confirm(payload: dict):
    # UEI-GridOn/1.0.0/on_confirm
    logger.info(f"BECKN STUB: Received on_confirm: {payload}")
    return {"message": {"ack": {"status": "ACK"}}}


@router.post("/uei/v1/search", response_model=BecknResponse, tags=["UEI"])
# TODO: UEI-Compliance - Implement Asynchronous Flow
# The current implementation is synchronous and returns the catalog directly.
# For full UEI compliance, this endpoint should:
# 1. Immediately return an ACK/NACK response.
# 2. Trigger a background task to assemble the catalog.
# 3. Make a POST request to the `on_search` endpoint specified in the `bap_uri`
#    of the original request body with the complete catalog.
async def search(
    request: BecknSearchRequest, services: BackgroundServices = Depends(get_services)
):
    """
    UEI-compliant search endpoint.
    Currently implemented synchronously for simulation purposes.
    """
    logger.info(f"API: Received UEI search request: {request.context.message_id}")
    workflow = services.workflow
    catalog = await workflow.build_catalog(request)

    response = BecknResponse(
        context=request.context,  # Echo back the context
        message=catalog
    )
    response.context.action = "on_search"
    response.context.bpp_id = workflow.state.settings.agent_id
    response.context.bpp_uri = workflow.state.settings.agent_uri

    return response
