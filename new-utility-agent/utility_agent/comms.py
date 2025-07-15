"""
Communications Module for the Utility Agent.

This module handles all outgoing HTTP-based communication with other agents.
It is designed to be a "swappable" component. To upgrade to a full A2A
protocol, you would replace the implementation of this class with one that
uses an A2A client, while keeping the method signatures the same.

The core business logic in the workflows should only call methods from this
module and remain agnostic to the underlying transport layer (HTTP, A2A, etc.).
"""
import httpx
import logging
from typing import Optional
from pydantic import ValidationError

from utility_agent.api.models import (
    RegisterDERPayload,
    HeartbeatPayload,
    AckPayload,
    CurtailmentCommand,
    SunSpecData,
)

# Configure logger
logger = logging.getLogger(__name__)

class CommunicationError(Exception):
    """Custom exception for communication failures."""
    pass

class UtilityCommsManager:
    """Manages outbound communication for the Utility Agent."""

    def __init__(self, timeout: int = 10):
        """
        Initializes the communications manager.
        Args:
            timeout: The default timeout in seconds for HTTP requests.
        """
        self._client = httpx.AsyncClient(timeout=timeout)
        logger.info("UtilityCommsManager initialized.")

    async def close(self):
        """Gracefully closes the HTTP client."""
        await self._client.aclose()
        logger.info("HTTP client closed.")

    async def send_curtailment_command(
        self, command: CurtailmentCommand, target_endpoint: str
    ) -> bool:
        """
        Sends a curtailment command to a specific DER agent.

        This function represents sending a 'curtailment_command' event.

        Args:
            command: The curtailment command payload.
            target_endpoint: The base URL of the target agent's API.

        Returns:
            True if the command was sent successfully (HTTP 2xx), False otherwise.
        """
        # Correctly construct the target URL
        target_url = f"{target_endpoint.rstrip('/')}/commands/curtail"
        
        logger.info(f"Sending curtailment command {command.command_id} to {target_url}")
        try:
            response = await self._client.post(target_url, json=command.model_dump(mode="json"))
            response.raise_for_status()
            logger.info(f"Successfully sent command {command.command_id}. Response: {response.json()}")
            return True
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP status error while sending command to {target_url}: {e.response.status_code} - {e.response.text}")
            raise CommunicationError(f"HTTP status error: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Request error while sending command to {target_url}: {e}")
            raise CommunicationError(f"HTTP request failed: {e}")

    async def get_sunspec_data(self, base_url: str) -> Optional[SunSpecData]:
        """Polls a DER agent's /status/sunspec endpoint to get its beliefs."""
        target_url = f"{base_url.rstrip('/')}/status/sunspec"
        logger.debug(f"Polling SunSpec data from {target_url}")
        try:
            response = await self._client.get(target_url)
            response.raise_for_status()
            # Validate the response against the Pydantic model
            return SunSpecData(**response.json())
        except httpx.HTTPStatusError as e:
            logger.warning(f"Failed to get SunSpec data from {target_url}. Status: {e.response.status_code}")
            return None
        except (httpx.RequestError, ValidationError) as e:
            logger.warning(f"Failed to get or validate SunSpec data from {target_url}: {e}")
            return None

    # Add other outbound communication methods as needed, for example:
    # async def send_beckn_on_search(self, response: BecknOnSearchResponse, target_uri: str):
    #     """Sends an on_search response to a Beckn BAP."""
    #     ... 