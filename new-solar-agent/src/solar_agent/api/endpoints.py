"""
FastAPI endpoints for the Solar Agent.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends

from solar_agent.api.models import (
    SolarAgentState,
    CurtailmentCommand,
    AckPayload,
    SimpleAck
)
from solar_agent.core.models import SunSpecData
from solar_agent.comms import SolarCommsManager
from solar_agent.workflow.graph import SolarWorkflow
from solar_agent.tools.data_generator import SunSpecDataGenerator

# Configure logger
logger = logging.getLogger(__name__)

# ==============================================================================
# Global Instances
# ==============================================================================
router = APIRouter()

# Create global instances for state and comms
state = SolarAgentState()
comms_manager = SolarCommsManager(utility_agent_url=state.utility_agent_url)

# The workflow manager now handles the adapter and data generator internally
workflow = SolarWorkflow(state, comms_manager)

# ==============================================================================
# Agent Status & Data Endpoints
# ==============================================================================

@router.get("/status", response_model=SolarAgentState, tags=["State"])
async def get_agent_state():
    """Returns the current internal state of the Solar Agent."""
    return state

@router.get("/status/sunspec", response_model=SunSpecData, tags=["State"])
async def get_sunspec_data():
    """Returns the latest simulated SunSpec data via the adapter."""
    return workflow.adapter.get_data()


# ==============================================================================
# Agent Command & Control Endpoints
# ==============================================================================

@router.post("/commands/curtail", response_model=AckPayload, tags=["Commands"])
async def receive_curtailment_command(command: CurtailmentCommand):
    """
    Receives a curtailment command from the utility agent and processes it
    through the agent's workflow.
    """
    logger.info(f"API: Received curtailment command {command.command_id}")
    ack = await workflow.handle_curtailment_command(command)
    return ack

# ==============================================================================
# Debugging Endpoints
# ==============================================================================

@router.post("/debug/set_fault", tags=["Debug"])
async def set_fault_mode():
    """Manually triggers a fault in the SunSpec data generator via the adapter."""
    logger.warning("DEBUG: Manually triggering fault condition.")
    # Access the generator through the workflow's adapter
    workflow.adapter.generator.trigger_fault()
    return {"status": "fault_triggered"}

@router.post("/beckn/trigger-search", response_model=SimpleAck, tags=["Beckn"])
async def trigger_beckn_search():
    """Manually triggers a Beckn search to find energy demand."""
    logger.info("API: Manually triggering Beckn search.")
    # This is now a background task so the API can return immediately
    await workflow.run_beckn_search()
    return SimpleAck(status="beckn_search_triggered") 

# TODO: UEI-Compliance - Implement /on_search Endpoint
# This endpoint is REQUIRED by the UEI spec for asynchronous discovery.
# The BPP (Utility Agent) will call this endpoint with the catalog.
# @router.post("/uei/v1/on_search", status_code=200)
# async def on_search(payload: dict):
#     """Receives the catalog from the BPP during UEI discovery."""
#     logger.info(f"Received /on_search callback with transaction ID: {payload.get('context', {}).get('transaction_id')}")
#     # Here, you would parse the catalog and update the agent's state/belief model.
#     # For example, store the received offers.
#     # state.beliefs["beckn_offers"] = payload['message']['catalog']
#     return {"message": {"ack": {"status": "ACK"}}} 