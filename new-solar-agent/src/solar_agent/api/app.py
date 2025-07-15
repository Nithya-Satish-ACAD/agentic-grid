"""
Main FastAPI application for the Solar Agent.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Configure logger
logger = logging.getLogger(__name__)

from solar_agent.api.endpoints import router, workflow, comms_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Starts the workflow on startup and stops it on shutdown.
    The adapter and data generator are managed by the workflow.
    """
    logger.info("Solar Agent API starting up...")

    # Start the adapter's data simulation (if any)
    workflow.adapter.generator.start()
    logger.info("SunSpec data generator started via adapter.")

    # Start the main agent workflow (registration, heartbeats, etc.)
    await workflow.run_registration()
    workflow.start_periodic_heartbeat()
    
    yield
    
    logger.info("Shutting down Solar Agent API...")
    
    # Stop the adapter's data simulation
    workflow.adapter.generator.stop()
    logger.info("SunSpec data generator stopped via adapter.")

    # Stop the workflow's background tasks
    workflow.stop()
    await comms_manager.close()

app = FastAPI(
    title="Solar Agent API",
    description="API for a simulated solar power agent.",
    lifespan=lifespan
)

app.include_router(router) 