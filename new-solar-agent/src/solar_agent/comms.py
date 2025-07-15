"""
Communications Module for the Solar Agent.

This module handles all outgoing HTTP-based communication to the Utility Agent.
It is designed as a "swappable" component. To upgrade to a full A2A
protocol, replace the implementation of this class with an A2A client,
while keeping the method signatures identical.
"""
import httpx
import logging
from typing import Optional

from solar_agent.api.models import (
    RegisterDERPayload,
    HeartbeatPayload,
    AckPayload,
)
from solar_agent.beckn import (
    BecknContext,
    BecknSearchRequest,
    BecknSearchMessage,
    BecknSearchIntent,
    BecknSearchItem,
    BecknSearchItemDescriptor,
    BecknSearchFulfillment,
    BecknSearchCustomer,
    BecknSearchPayment,
)
from .core.config import settings

# Configure logger
logger = logging.getLogger(__name__)

class CommunicationError(Exception):
    """Custom exception for communication failures."""
    pass

class SolarCommsManager:
    """Manages outbound communication for the Solar Agent."""

    def __init__(self, utility_agent_url: str = settings.utility_agent_url, agent_id: str = settings.agent_id, timeout: int = 10):
        """
        Initializes the communications manager.
        Args:
            utility_agent_url: The base URL of the Utility Agent API.
            agent_id: The ID of this agent.
            timeout: The default timeout in seconds for HTTP requests.
        """
        if not utility_agent_url:
            raise ValueError("utility_agent_url cannot be empty.")
        self.utility_agent_url = utility_agent_url
        self.agent_id = agent_id
        self._client = httpx.AsyncClient(timeout=timeout)
        logger.info(f"SolarCommsManager initialized for Utility Agent at {self.utility_agent_url}")

    async def close(self):
        """Gracefully closes the HTTP client."""
        await self._client.aclose()
        logger.info("HTTP client closed.")

    async def _post(self, endpoint: str, payload: dict) -> dict:
        """Helper method for making POST requests."""
        url = f"{self.utility_agent_url}{endpoint}"
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Failed to send request to {url}. Error: {e}")
            raise CommunicationError(f"HTTP request failed: {e}") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"Received non-2xx response from {url}. Status: {e.response.status_code}")
            # Specific check for Beckn ACK response which might have details
            if "uei/v1/search" in url:
                 logger.error(f"Utility response body: {e.response.text}")

            raise CommunicationError(f"HTTP status error: {e.response.status_code}") from e

    async def send_registration(self, payload: RegisterDERPayload) -> bool:
        """
        Sends a registration request to the Utility Agent.
        This function represents sending a 'register_der' event.
        """
        target_url = f"{self.utility_agent_url}/register_der"
        logger.info(f"Sending registration for agent {payload.id}...")
        try:
            response = await self._client.post(target_url, json=payload.model_dump(mode="json"))
            response.raise_for_status()  # Raises on 4xx/5xx responses
            logger.info(f"Registration successful: {response.json().get('status')}")
            return response.json().get("status") == "success"
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Failed to register agent {payload.id}. Error: {e}")
            return False

    async def send_heartbeat(self, payload: HeartbeatPayload) -> bool:
        """Sends a heartbeat to the Utility Agent."""
        target_url = f"{self.utility_agent_url}/heartbeat"
        logger.debug(f"Sending heartbeat for agent {payload.id}...")
        try:
            response = await self._client.post(target_url, json=payload.model_dump(mode="json"))
            response.raise_for_status()
            logger.info(f"Heartbeat successful: {response.json().get('status')}")
            return response.json().get("status") == "ok"
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.warning(f"Failed to send heartbeat for agent {payload.id}. Error: {e}")
            return False

    async def send_ack(self, payload: AckPayload) -> bool:
        """Sends an acknowledgement to the Utility Agent."""
        target_url = f"{self.utility_agent_url}/ack"
        logger.info(f"Sending ACK for command {payload.command_id} from agent {payload.agent_id}...")
        try:
            response = await self._client.post(target_url, json=payload.model_dump(mode="json"))
            response.raise_for_status()
            logger.info("ACK sent successfully.")
            return response.json().get("status") == "acknowledged"
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Failed to send ACK for command {payload.command_id}. Error: {e}")
            return False

    async def send_beckn_search(self, payload: BecknSearchRequest) -> bool:
        """
        Sends a Beckn search request to the Utility Agent.
        The Utility Agent will respond with an immediate ACK. The actual
        search results will come later via a callback to an 'on_search' endpoint.
        """
        target_url = f"{self.utility_agent_url}/uei/v1/search"
        logger.info(f"Sending Beckn search request (message_id: {payload.context.message_id})...")
        try:
            response = await self._client.post(target_url, json=payload.model_dump(mode="json"))
            response.raise_for_status()
            # We expect a simple ACK in the immediate response
            ack_status = response.json().get("message", {}).get("ack", {}).get("status") == "ACK"
            if not ack_status:
                 logger.warning(f"Beckn search request was not acknowledged by the utility. Response: {response.json()}")
            return ack_status
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Communication failed while sending Beckn search request: {e}")
            return False

    def _create_beckn_search_request(self) -> BecknSearchRequest:
        """Creates a Beckn search request payload."""
        context = BecknContext(
            domain="dsep:energy",
            country="IND",
            city="std:080",
            action="search",
            core_version="1.0.0",
            bap_id=self.agent_id,
            bap_uri=f"http://localhost:8001/beckn/on_search",  # The solar agent's callback endpoint
            bpp_id="utility-agent-001",  # The ID of the utility agent we are searching
            bpp_uri=self.utility_agent_url,  # The base URI of the utility agent
        )
        message = BecknSearchMessage(
            intent=BecknSearchIntent(
                item=BecknSearchItem(descriptor=BecknSearchItemDescriptor(name="Rooftop Solar")),
                fulfillment=BecknSearchFulfillment(
                    customer=BecknSearchCustomer(
                        id=self.agent_id,  # Our agent is the customer
                    )
                ),
                payment=BecknSearchPayment(collection_amount="0"),
            )
        )
        return BecknSearchRequest(context=context, message=message) 