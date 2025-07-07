"""FastAPI module for Solar Agent REST endpoints."""

from .endpoints import router
from .models import (
    CurtailmentRequest,
    StatusResponse,
    HealthResponse,
    AlertRequest,
)

__all__ = [
    "router",
    "CurtailmentRequest",
    "StatusResponse", 
    "HealthResponse",
    "AlertRequest",
] 