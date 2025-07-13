from fastapi import FastAPI
from ..config import Config
from ..logging_config import setup_logging
from .endpoints import router as api_router
import logging
from .endpoints import state, logger  # Import shared state and logger from endpoints
from contextlib import asynccontextmanager

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Utility Agent API started")
    yield  # Add shutdown logic here if needed

app = FastAPI(title="Utility Agent API", version="0.1.0", lifespan=lifespan)

app.include_router(api_router, prefix="/api")

@app.get("/metrics")
async def metrics():
    # Basic metrics stub (expand with prometheus later)
    return {"active_ders": len(state.registered_ders), "alerts_count": len(state.alerts)}
