"""
Solar Agent - Production-grade Solar Agent backend for distributed multi-agent energy grid system.

This package provides:
- LangGraph workflow orchestration for solar operations
- FastAPI REST endpoints for agent communication
- Hardware adapter abstraction for SunSpec and other protocols
- State persistence and recovery capabilities
- Human-in-the-loop support for critical operations
"""

__version__ = "0.1.0"
__author__ = "Solar Grid Team"
__email__ = "team@solargrid.com"

from solar_agent.core.config import Settings
from solar_agent.core.models import AgentStatus, SolarData

__all__ = [
    "Settings",
    "AgentStatus", 
    "SolarData",
] 