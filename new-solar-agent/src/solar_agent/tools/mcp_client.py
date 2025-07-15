"""MCP client for weather data integration."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import websockets
from solar_agent.core.config import settings
from solar_agent.core.exceptions import MCPException


logger = logging.getLogger(__name__)


class MCPClient:
    """Model Context Protocol client for external integrations."""
    
    def __init__(self, server_url: str = None, timeout: int = None):
        """Initialize MCP client.
        
        Args:
            server_url: MCP server WebSocket URL
            timeout: Request timeout in seconds
        """
        self.server_url = server_url or settings.mcp_weather_server_url
        self.timeout = timeout or settings.mcp_timeout
        self.websocket = None
        self.is_connected = False
        
    async def connect(self) -> bool:
        """Connect to MCP server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.websocket = await websockets.connect(
                self.server_url,
                timeout=self.timeout
            )
            self.is_connected = True
            logger.info(f"Connected to MCP server at {self.server_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
        self.is_connected = False
        logger.info("Disconnected from MCP server")
    
    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send request to MCP server.
        
        Args:
            method: MCP method name
            params: Request parameters
            
        Returns:
            Response dictionary
            
        Raises:
            MCPException: If request fails
        """
        if not self.is_connected or not self.websocket:
            raise MCPException(
                "Not connected to MCP server",
                server_url=self.server_url,
                operation=method
            )
        
        # Prepare MCP request
        request = {
            "jsonrpc": "2.0",
            "id": f"req_{datetime.utcnow().timestamp()}",
            "method": method,
            "params": params or {}
        }
        
        try:
            # Send request
            await asyncio.wait_for(
                self.websocket.send(json.dumps(request)),
                timeout=self.timeout
            )
            
            # Receive response
            response_text = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=self.timeout
            )
            
            response = json.loads(response_text)
            
            # Check for errors
            if "error" in response:
                raise MCPException(
                    f"MCP server error: {response['error']}",
                    server_url=self.server_url,
                    operation=method,
                    details=response["error"]
                )
            
            return response.get("result", {})
            
        except asyncio.TimeoutError:
            raise MCPException(
                "MCP request timeout",
                server_url=self.server_url,
                operation=method,
                error_code="TIMEOUT"
            )
        except Exception as e:
            raise MCPException(
                f"MCP request failed: {str(e)}",
                server_url=self.server_url,
                operation=method,
                details={"error": str(e)}
            )
    
    async def get_weather_forecast(
        self, 
        location: str = None,
        hours: int = 1
    ) -> Dict[str, Any]:
        """Get weather forecast data.
        
        Args:
            location: Location identifier (defaults to agent location)
            hours: Number of hours to forecast
            
        Returns:
            Weather forecast data
        """
        location = location or settings.location
        
        params = {
            "location": location,
            "hours": hours,
            "include": ["temperature", "humidity", "cloud_cover", "wind_speed", "irradiance"]
        }
        
        return await self.send_request("weather.forecast", params)
    
    async def get_current_weather(self, location: str = None) -> Dict[str, Any]:
        """Get current weather conditions.
        
        Args:
            location: Location identifier
            
        Returns:
            Current weather data
        """
        location = location or settings.location
        
        params = {
            "location": location,
            "include": ["temperature", "humidity", "cloud_cover", "wind_speed", "irradiance"]
        }
        
        return await self.send_request("weather.current", params)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


# Global MCP client instance
_mcp_client = None


async def get_mcp_client() -> MCPClient:
    """Get or create global MCP client instance.
    
    Returns:
        MCPClient instance
    """
    global _mcp_client
    
    if _mcp_client is None:
        _mcp_client = MCPClient()
    
    if not _mcp_client.is_connected:
        await _mcp_client.connect()
    
    return _mcp_client


async def get_weather_data(location: str = None) -> Optional[Dict[str, Any]]:
    """Get weather data for forecasting.
    
    This is a convenience function that handles MCP client connection
    and error handling automatically.
    
    Args:
        location: Location identifier
        
    Returns:
        Weather data dictionary or None if unavailable
    """
    try:
        async with MCPClient() as client:
            weather_data = await client.get_current_weather(location)
            
            # Normalize weather data format
            normalized_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "cloud_cover_percent": weather_data.get("cloud_cover", 0),
                "temperature_c": weather_data.get("temperature", 25),
                "humidity_percent": weather_data.get("humidity", 50),
                "wind_speed_ms": weather_data.get("wind_speed", 0),
                "irradiance_forecast_w_m2": weather_data.get("irradiance", 800),
            }
            
            logger.info("Retrieved weather data from MCP server")
            return normalized_data
            
    except MCPException as e:
        logger.warning(f"MCP weather request failed: {e.message}")
        return None
    except Exception as e:
        logger.warning(f"Error getting weather data: {e}")
        return None


async def get_weather_forecast_data(
    location: str = None,
    hours: int = 1
) -> Optional[Dict[str, Any]]:
    """Get weather forecast data for the specified period.
    
    Args:
        location: Location identifier
        hours: Number of hours to forecast
        
    Returns:
        Weather forecast data or None if unavailable
    """
    try:
        async with MCPClient() as client:
            forecast_data = await client.get_weather_forecast(location, hours)
            
            # Extract forecast for the next hour (or average if multiple hours)
            if isinstance(forecast_data, list) and forecast_data:
                # Take the first forecast period
                next_hour = forecast_data[0]
            elif isinstance(forecast_data, dict):
                next_hour = forecast_data
            else:
                logger.warning("Unexpected weather forecast format")
                return None
            
            # Normalize forecast data
            normalized_forecast = {
                "timestamp": datetime.utcnow().isoformat(),
                "cloud_cover_percent": next_hour.get("cloud_cover", 0),
                "temperature_c": next_hour.get("temperature", 25),
                "humidity_percent": next_hour.get("humidity", 50),
                "wind_speed_ms": next_hour.get("wind_speed", 0),
                "irradiance_forecast_w_m2": next_hour.get("irradiance", 800),
                "forecast_period_hours": hours,
            }
            
            logger.info(f"Retrieved {hours}h weather forecast from MCP server")
            return normalized_forecast
            
    except MCPException as e:
        logger.warning(f"MCP weather forecast request failed: {e.message}")
        return None
    except Exception as e:
        logger.warning(f"Error getting weather forecast: {e}")
        return None


def create_mock_weather_data(
    cloud_cover: float = 20.0,
    temperature: float = 25.0,
    wind_speed: float = 5.0
) -> Dict[str, Any]:
    """Create mock weather data for testing when MCP server is not available.
    
    Args:
        cloud_cover: Cloud cover percentage (0-100)
        temperature: Temperature in Celsius
        wind_speed: Wind speed in m/s
        
    Returns:
        Mock weather data dictionary
    """
    # Calculate irradiance based on cloud cover and time of day
    hour = datetime.utcnow().hour
    
    if 6 <= hour <= 18:
        # Daylight hours - calculate base irradiance
        import math
        solar_noon = 12.0
        time_factor = math.exp(-0.5 * ((hour - solar_noon) / 3) ** 2)
        base_irradiance = 1000 * time_factor
        
        # Reduce by cloud cover
        cloud_factor = 1.0 - (cloud_cover / 100.0) * 0.8  # Clouds reduce by up to 80%
        irradiance = base_irradiance * cloud_factor
    else:
        # Night time
        irradiance = 0
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "cloud_cover_percent": cloud_cover,
        "temperature_c": temperature,
        "humidity_percent": 50.0 + (cloud_cover / 100.0) * 30.0,  # Higher humidity with clouds
        "wind_speed_ms": wind_speed,
        "irradiance_forecast_w_m2": max(0, irradiance),
        "source": "mock",
    } 