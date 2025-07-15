"""Hardware adapter module for Solar Agent."""

from .base import BaseAdapter, HardwareAdapter
from .mock import MockAdapter
from solar_agent.core.config import settings

def get_adapter() -> MockAdapter:
    """Return the mock hardware adapter."""
    config = {
        "nameplate_power": getattr(settings, "nameplate_power", 5000.0),
        "fault_probability": getattr(settings, "fault_probability", 0.01),
    }
    return MockAdapter(config)

__all__ = [
    "BaseAdapter",
    "HardwareAdapter",
    "MockAdapter",
    "get_adapter",
] 