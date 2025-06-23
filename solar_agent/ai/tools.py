"""
AI tools for external service interactions.

This module provides tools for weather MCP calls and LLM interactions
with timeout handling and schema validation.
See backend-structure.md for detailed specification.
"""

import asyncio
import json
from typing import Dict, Any, Optional
import httpx
from openai import AsyncOpenAI


class WeatherMCPTool:
    """Tool for interacting with Weather MCP server."""
    
    def __init__(self, mcp_url: str, timeout: int = 30):
        """
        Initialize Weather MCP tool.
        
        Args:
            mcp_url: URL of the Weather MCP server
            timeout: Request timeout in seconds
        """
        self.mcp_url = mcp_url
        self.timeout = timeout
        
    async def get_weather(self, 
                         location: Dict[str, float], 
                         horizon_hours: int = 24) -> Dict[str, Any]:
        """
        Get weather data from MCP server.
        
        Args:
            location: Dictionary with lat, lon coordinates
            horizon_hours: Hours into the future to forecast
            
        Returns:
            Weather data dictionary
        """
        # TODO: Implement JSON-RPC call to Weather MCP
        # TODO: Add response schema validation
        # TODO: Add caching layer
        
        payload = {
            "jsonrpc": "2.0",
            "method": "get_weather",
            "params": {
                "location": location,
                "horizon_hours": horizon_hours
            },
            "id": 1
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.mcp_url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                if "error" in result:
                    raise Exception(f"MCP Error: {result['error']}")
                    
                return result.get("result", {})
                
        except Exception as e:
            # TODO: Add proper error handling and logging
            print(f"Error calling Weather MCP: {e}")
            return {}


class LLMTool:
    """Tool for LLM interactions."""
    
    def __init__(self, api_key: str, model: str = "gpt-4", timeout: int = 60):
        """
        Initialize LLM tool.
        
        Args:
            api_key: OpenAI API key
            model: Model to use for completions
            timeout: Request timeout in seconds
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.timeout = timeout
        
    async def generate_response(self, 
                              prompt: str, 
                              max_tokens: int = 1000) -> str:
        """
        Generate LLM response.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text response
        """
        # TODO: Add proper error handling
        # TODO: Add response validation
        # TODO: Add retry logic with backoff
        
        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens
                ),
                timeout=self.timeout
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            # TODO: Add proper error handling and logging
            print(f"Error calling LLM: {e}")
            return ""
            
    async def generate_structured_response(self, 
                                         prompt: str, 
                                         schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate structured JSON response from LLM.
        
        Args:
            prompt: Input prompt
            schema: Expected JSON schema
            
        Returns:
            Parsed JSON response
        """
        # TODO: Add schema validation
        # TODO: Add JSON parsing with fallback
        
        response_text = await self.generate_response(prompt)
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # TODO: Add fallback parsing or error handling
            return {} 