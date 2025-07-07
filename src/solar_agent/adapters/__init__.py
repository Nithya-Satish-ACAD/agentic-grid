"""Hardware adapter module for Solar Agent."""

from .base import HardwareAdapter
from .mock import MockAdapter
from .sunspec import SunSpecAdapter
from solar_agent.core.config import settings

def get_adapter():
    """Return the appropriate hardware adapter based on config."""
    config = {
        "capacity_kw": getattr(settings, "capacity_kw", 100.0),
        "fault_probability": getattr(settings, "fault_probability", 0.001),
        # Add more config fields as needed
    }
    if getattr(settings, "USE_MOCK_ADAPTER", True):
        return MockAdapter(config)
    else:
        return SunSpecAdapter(config)

__all__ = [
    "HardwareAdapter",
    "MockAdapter",
    "SunSpecAdapter",
    "get_adapter",
] 