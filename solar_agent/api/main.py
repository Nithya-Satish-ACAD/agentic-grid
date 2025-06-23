"""
FastAPI application for Solar Agent.

This module creates the FastAPI app with middleware, routes,
and startup/shutdown event handlers.
See backend-structure.md for detailed specification.
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
from ..models.config import get_config
from ..utils.logging import configure_logging, get_logger
from ..utils.metrics import metrics
from ..core.scheduler import Scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger = get_logger("solar_agent")
    logger.info("Starting Solar Agent")
    
    # Initialize components
    config = get_config()
    
    # TODO: Initialize adapter, clients, AI components
    # TODO: Start scheduler with periodic tasks
    # TODO: Register agent with Utility
    
    logger.info("Solar Agent started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Solar Agent")
    
    # TODO: Stop scheduler
    # TODO: Cleanup resources
    # TODO: Deregister agent if needed
    
    logger.info("Solar Agent shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    # Get configuration
    config = get_config()
    
    # Configure logging
    configure_logging(config)
    
    # Create FastAPI app
    app = FastAPI(
        title="Solar Agent",
        description="Solar power monitoring and forecasting agent",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Configure properly for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add correlation ID middleware
    @app.middleware("http")
    async def add_correlation_id(request: Request, call_next):
        """Add correlation ID to response headers."""
        from ..utils.correlation import extract_correlation_id_from_headers, set_correlation_id
        
        # Extract correlation ID from request
        correlation_id = extract_correlation_id_from_headers(dict(request.headers))
        if correlation_id:
            set_correlation_id(correlation_id)
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        if correlation_id:
            response.headers["X-Correlation-ID"] = correlation_id
            
        return response
    
    # Include routers
    app.include_router(router, prefix="/api/v1")
    
    # Add metrics endpoint
    @app.get("/metrics")
    async def metrics_endpoint():
        """Prometheus metrics endpoint."""
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    return app


def get_app() -> FastAPI:
    """
    Get the FastAPI application instance.
    
    Returns:
        FastAPI application instance
    """
    return create_app()


# Only create app instance when running as main
if __name__ == "__main__":
    app = create_app()
else:
    app = None 