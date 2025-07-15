"""Tools package for Solar Agent."""

# Always import basic tools
from .data_generator import SunSpecDataGenerator

# Try to import LLM-dependent tools
try:
    from .forecasting import SolarForecaster, generate_forecast
    FORECASTING_AVAILABLE = True
except ImportError as e:
    # LLM dependencies not available
    print(f"Forecasting tools not available: {e}")
    SolarForecaster = None
    generate_forecast = None
    FORECASTING_AVAILABLE = False

try:
    from .mcp_client import MCPClient
    MCP_AVAILABLE = True
except ImportError as e:
    # MCP dependencies not available  
    print(f"MCP tools not available: {e}")
    MCPClient = None
    MCP_AVAILABLE = False

# Export available tools
__all__ = [
    "SunSpecDataGenerator",
    "FORECASTING_AVAILABLE",
    "MCP_AVAILABLE"
]

# Add optional exports if available
if FORECASTING_AVAILABLE:
    __all__.extend(["SolarForecaster", "generate_forecast"])

if MCP_AVAILABLE:
    __all__.extend(["MCPClient"]) 