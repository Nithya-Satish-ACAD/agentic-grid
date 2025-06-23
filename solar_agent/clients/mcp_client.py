"""
MCP client for Weather MCP server interactions.

This module provides a client for Weather MCP server with caching,
schema validation, and error handling.
See backend-structure.md for detailed specification.
"""

import time
from typing import Dict, Any, Optional
from ..ai.tools import WeatherMCPTool


class MCPClient:
    """Client for Weather MCP server with caching."""
    
    def __init__(self, 
                 mcp_url: str,
                 cache_ttl: int = 300,  # 5 minutes
                 timeout: int = 30):
        """
        Initialize MCP client.
        
        Args:
            mcp_url: URL of Weather MCP server
            cache_ttl: Cache TTL in seconds
            timeout: Request timeout in seconds
        """
        self.weather_tool = WeatherMCPTool(mcp_url, timeout)
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        
    async def get_weather(self, 
                         location: Dict[str, float], 
                         horizon_hours: int = 24) -> Dict[str, Any]:
        """
        Get weather data with caching.
        
        Args:
            location: Dictionary with lat, lon coordinates
            horizon_hours: Hours into the future to forecast
            
        Returns:
            Weather data dictionary
        """
        cache_key = self._generate_cache_key(location, horizon_hours)
        
        # Check cache
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
            
        # Fetch from MCP server
        weather_data = await self.weather_tool.get_weather(location, horizon_hours)
        
        # Validate and cache
        if self._validate_weather_data(weather_data):
            self._cache_data(cache_key, weather_data)
            return weather_data
        else:
            # TODO: Add proper error handling for invalid data
            print("Invalid weather data received from MCP")
            return {}
            
    def _generate_cache_key(self, 
                           location: Dict[str, float], 
                           horizon_hours: int) -> str:
        """Generate cache key for location and horizon."""
        lat = location.get('lat', 0)
        lon = location.get('lon', 0)
        return f"weather_{lat}_{lon}_{horizon_hours}"
        
    def _get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache if valid."""
        if cache_key not in self._cache:
            return None
            
        cache_entry = self._cache[cache_key]
        if time.time() - cache_entry['timestamp'] < self.cache_ttl:
            return cache_entry['data']
            
        # Remove expired entry
        del self._cache[cache_key]
        return None
        
    def _cache_data(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Cache weather data."""
        self._cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
        
    def _validate_weather_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate weather data structure.
        
        Args:
            data: Weather data to validate
            
        Returns:
            True if data is valid
        """
        # TODO: Implement comprehensive schema validation
        # TODO: Add Pydantic model for weather data
        
        if not isinstance(data, dict):
            return False
            
        # Basic validation - check for required fields
        required_fields = ['temperature', 'conditions']
        return all(field in data for field in required_fields)
        
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0
        
        for entry in self._cache.values():
            if current_time - entry['timestamp'] < self.cache_ttl:
                valid_entries += 1
            else:
                expired_entries += 1
                
        return {
            'total_entries': len(self._cache),
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'cache_ttl': self.cache_ttl
        } 