"""
FastAPI endpoints for the Beckn/UEI protocol.

This module provides the server-side implementation for the BAP (Beckn Application Platform)
role, which in our case is the Utility Agent. It exposes endpoints that other agents
(acting as BPPs) can call.
"""
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
import asyncio

from .protocol import SearchRequest, OnSearchRequest, BecknResponse

logger = logging.getLogger(__name__)

# A router for all Beckn-related endpoints
beckn_router = APIRouter(prefix="/uei/v1", tags=["Beckn Protocol"])


async def send_on_search_callback(on_search_payload: OnSearchRequest):
    """
    Simulates sending an asynchronous 'on_search' response back to the BAP.
    In a real implementation, this would use an HTTP client to POST the
    response to the bap_uri found in the original request's context.
    """
    logger.info(f"Simulating sending on_search to BAP. Transaction ID: {on_search_payload.context.transaction_id}")
    # Here you would add `httpx.post(bap_uri, json=on_search_payload.dict())`
    await asyncio.sleep(2) # Simulate network delay
    logger.info("on_search callback simulation complete.")


@beckn_router.post("/search", response_model=BecknResponse)
async def search(request: SearchRequest, background_tasks: BackgroundTasks):
    """
    Receives a search request from a BAP (e.g., a Solar Agent looking to sell power).
    It acknowledges the request immediately and then processes the search in the background.
    """
    logger.info(f"Received Beckn search request. Transaction ID: {request.context.transaction_id}")

    # --- 1. Acknowledge the request immediately ---
    # This is standard Beckn practice. The real response comes later via a callback.
    ack_response = {"message": {"ack": {"status": "ACK"}}}

    # --- 2. Create the 'on_search' response ---
    # In a real implementation, this would involve querying a database or an internal
    # state to find matching services (e.g., demand for power).
    # For now, we'll create a hardcoded stub response.
    on_search_context = request.context.copy(update={"action": "on_search"})
    
    on_search_payload = OnSearchRequest(
        context=on_search_context,
        message={
            "catalog": {
                "descriptor": {"name": "Utility Agent Energy Catalog"},
                "providers": [
                    {
                        "id": "utility-agent-001",
                        "descriptor": {"name": "Local Utility Demand"},
                        "items": [
                            {
                                "id": "demand-item-001",
                                "descriptor": {"name": "1-hour block of demand response"},
                                "price": {"currency": "INR", "value": "3.50"},
                                "fulfillment_id": "fulfillment-001"
                            }
                        ]
                    }
                ]
            }
        }
    )

    # --- 3. Schedule the 'on_search' callback to run in the background ---
    background_tasks.add_task(send_on_search_callback, on_search_payload)

    return ack_response 