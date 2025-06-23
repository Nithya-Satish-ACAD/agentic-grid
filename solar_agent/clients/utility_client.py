"""
Utility client for communicating with Utility Agent.

This module provides HTTP client functionality for posting forecasts,
alerts, and status updates to the Utility Agent with retry/backoff logic.
See backend-structure.md for detailed specification.
"""

import asyncio
from typing import Dict, Any, Optional
import httpx
from ..models.schemas import (
    RegisterPayload, 
    StatusPayload, 
    ForecastPayload, 
    AlertPayload
)


class UtilityClient:
    """HTTP client for Utility Agent communication."""
    
    def __init__(self, 
                 base_url: str, 
                 api_key: str,
                 timeout: int = 30,
                 max_retries: int = 3):
        """
        Initialize utility client.
        
        Args:
            base_url: Base URL of Utility Agent
            api_key: API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    async def register_agent(self, payload: RegisterPayload) -> bool:
        """
        Register agent with Utility.
        
        Args:
            payload: Registration payload
            
        Returns:
            True if registration successful
        """
        return await self._post_with_retry(
            "/agents/register", 
            payload.model_dump()
        )
        
    async def post_status(self, payload: StatusPayload) -> bool:
        """
        Post status update to Utility.
        
        Args:
            payload: Status payload
            
        Returns:
            True if status update successful
        """
        return await self._post_with_retry(
            f"/agents/{payload.agent_id}/status",
            payload.model_dump()
        )
        
    async def post_forecast(self, payload: ForecastPayload) -> bool:
        """
        Post forecast to Utility.
        
        Args:
            payload: Forecast payload
            
        Returns:
            True if forecast posted successfully
        """
        return await self._post_with_retry(
            f"/agents/{payload.agent_id}/forecast",
            payload.model_dump()
        )
        
    async def post_alert(self, payload: AlertPayload) -> bool:
        """
        Post alert to Utility.
        
        Args:
            payload: Alert payload
            
        Returns:
            True if alert posted successfully
        """
        return await self._post_with_retry(
            f"/agents/{payload.agent_id}/alerts",
            payload.model_dump()
        )
        
    async def _post_with_retry(self, 
                              endpoint: str, 
                              data: Dict[str, Any]) -> bool:
        """
        POST request with retry logic and exponential backoff.
        
        Args:
            endpoint: API endpoint path
            data: Request data
            
        Returns:
            True if request successful
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        url, 
                        json=data, 
                        headers=self.headers
                    )
                    response.raise_for_status()
                    return True
                    
            except httpx.HTTPStatusError as e:
                # TODO: Add proper error handling and logging
                print(f"HTTP error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries:
                    return False
                    
            except Exception as e:
                # TODO: Add proper error handling and logging
                print(f"Request error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries:
                    return False
                    
            # Exponential backoff
            if attempt < self.max_retries:
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
                
        return False 