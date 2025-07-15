"""
Main FastAPI application for the Utility Agent.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, BackgroundTasks
from dotenv import load_dotenv

load_dotenv()

from .endpoints import router as api_router
from utility_agent.api.models import UtilityState
from utility_agent.comms import UtilityCommsManager
from utility_agent.workflow.graph import UtilityWorkflow
from ..logging_config import setup_logging
from ..beckn.endpoints import beckn_router # Import the new Beckn router

# Configure logger
setup_logging()
logger = logging.getLogger(__name__)

# Create singleton instances of the core components
state = UtilityState()
comms_manager = UtilityCommsManager()
workflow = UtilityWorkflow(state, comms_manager)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Utility Agent API starting up...")
    app.state.workflow = workflow
    app.state.comms_manager = comms_manager
    workflow.start_comprehension_loop()
    yield
    # Shutdown logic
    logger.info("Utility Agent API shutting down...")
    workflow.stop()

# Main FastAPI app instance
app = FastAPI(
    title="Utility Agent API",
    description="API for the Utility Agent in the P2P Energy Grid.",
    lifespan=lifespan,
)

app.include_router(api_router)
app.include_router(beckn_router)
