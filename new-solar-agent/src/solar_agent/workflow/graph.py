"""
This module defines the core workflow logic for the Solar Agent.
"""
import asyncio
import logging
from typing import Optional

from solar_agent.api.models import SolarAgentState, CurtailmentCommand, AckPayload, RegisterDERPayload, HeartbeatPayload
from solar_agent.adapters import BaseAdapter, get_adapter
from solar_agent.core.models import SunSpecData
from solar_agent.comms import SolarCommsManager, CommunicationError
from solar_agent.beckn import BecknContext, BecknSearchIntent, BecknSearchMessage, BecknSearchRequest
from solar_agent.core.config import settings

logger = logging.getLogger(__name__)

class SolarWorkflow:
    """
    Orchestrates the Solar Agent's main behaviors, such as registration,
    sending heartbeats, and processing commands from the Utility Agent.
    """

    def __init__(self, state: SolarAgentState, comms_manager: SolarCommsManager):
        """
        Initializes the workflow.
        Args:
            state: The shared state object for the agent.
            comms_manager: The manager for outbound communication.
        """
        self.state = state
        self.comms_manager = comms_manager
        self.adapter = get_adapter()
        self._heartbeat_task: Optional[asyncio.Task] = None
        self.heartbeat_interval_seconds = 30

    async def run_registration(self):
        """
        Attempts to register this agent with the Utility Agent until successful.
        """
        logger.info("WORKFLOW: Kicking off registration process...")
        if self.state.is_registered:
            logger.info("Agent is already registered.")
            return

        payload = RegisterDERPayload(
            id=self.state.agent_id,
            type="solar",
            api_endpoint=f"http://{settings.host}:{settings.port}"
        )
        try:
            success = await self.comms_manager.send_registration(payload)
            if success:
                self.state.is_registered = True
                logger.info("Registration successful.")
            else:
                logger.error("Registration failed. Received non-success status from utility.")
        except CommunicationError as e:
            logger.error(f"Failed to register due to communication error: {e}")

    async def run_beckn_search(self):
        """
        Initiates a Beckn search request to discover energy demand from the Utility Agent.
        """
        logger.info("WORKFLOW: Initiating Beckn search for energy demand.")
        
        # 1. Create the Beckn request payload
        # The BAP (us) is the Solar Agent. The BPP (them) is the Utility Agent.
        context = BecknContext(
            bap_id=self.state.agent_id,
            bap_uri=f"http://localhost:8001/beckn/on_search", # This agent's callback URL
            bpp_id="utility-agent.example.com", # The ID of the BPP we are calling
            bpp_uri=self.comms_manager.utility_agent_url # The base URL of the BPP
        )
        intent = BecknSearchIntent(
            item={"descriptor": {"name": "r-APPC"}},
            fulfillment={
                "customer": {"id": self.state.agent_id},
                "type": "delivery",
                "start": {"time": {"timestamp": "2025-07-16T10:00:00Z"}},
                "end": {"time": {"timestamp": "2025-07-16T11:00:00Z"}},
            },
            payment={"collection_amount": "0"} # Add required payment field
        )
        payload = BecknSearchRequest(context=context, message=BecknSearchMessage(intent=intent))

        # 2. Use the comms manager to send the request
        try:
            success = await self.comms_manager.send_beckn_search(payload)
            if success:
                logger.info("Successfully sent Beckn search request and received ACK.")
            else:
                logger.warning("Beckn search request was not acknowledged by the utility.")
        except CommunicationError as e:
            logger.error(f"Failed to send Beckn search due to communication error: {e}")

        # TODO: UEI-Compliance - Implement Asynchronous Flow
        # The current implementation is synchronous and expects the catalog
        # directly in the response. For full UEI compliance, this node should:
        # 1. Call the /search endpoint.
        # 2. Receive an ACK/NACK.
        # 3. Wait for a callback on a new /on_search endpoint.
        # 4. The /on_search endpoint would then receive the catalog and update the state.
        response_json = await comms.trigger_beckn_search(
            utility_agent_url=state.settings.utility_agent_url,
            payload=beckn_payload
        )

    def start_periodic_heartbeat(self):
        """Starts the background task that sends periodic heartbeats."""
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            logger.info(f"Starting periodic heartbeat every {self.heartbeat_interval_seconds} seconds.")

    async def _heartbeat_loop(self):
        """The main loop for sending heartbeats periodically."""
        while True:
            if self.state.is_registered:
                payload = HeartbeatPayload(id=self.state.agent_id)
                try:
                    await self.comms_manager.send_heartbeat(payload)
                    self.state.last_heartbeat = payload.timestamp
                except CommunicationError as e:
                    logger.warning(f"Failed to send heartbeat: {e}")
            await asyncio.sleep(self.heartbeat_interval_seconds)

    def stop(self):
        """Stops any running background tasks managed by the workflow."""
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            logger.info("Heartbeat task cancelled.")

    async def handle_curtailment_command(self, command: CurtailmentCommand) -> AckPayload:
        """
        Processes an incoming curtailment command and sends an acknowledgement.
        """
        logger.info(f"WORKFLOW: Handling curtailment command {command.command_id}")
        
        self.adapter.set_curtailment(command.curtailment_kw)

        # We should also clear the fault on the device
        self.adapter.clear_fault()

        # The state should be updated by reading from the adapter, not by direct manipulation
        updated_data = self.adapter.get_data()
        self.state.power_output_kw = updated_data.ac_power

        ack_payload = AckPayload(
            command_id=command.command_id,
            agent_id=self.state.agent_id,
            status="success",
            message=f"Curtailment acknowledged. New output is {self.state.power_output_kw} kW."
        )

        try:
            await self.comms_manager.send_ack(ack_payload)
            logger.info(f"Successfully sent ACK for command {command.command_id}")
        except CommunicationError as e:
            logger.error(f"Failed to send ACK for command {command.command_id}: {e}")

        return ack_payload 