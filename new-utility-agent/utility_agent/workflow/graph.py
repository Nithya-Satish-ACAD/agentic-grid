"""
This module defines the core workflow logic for the Utility Agent.
"""
import asyncio
import logging
from datetime import datetime
import textwrap
import uuid
import json

from langgraph.graph import StateGraph, END
from utility_agent.api.models import UtilityState, DERStatus, SunSpecData, CurtailmentCommand
from utility_agent.comms import UtilityCommsManager
from ..llm.factory import get_llm_provider


logger = logging.getLogger(__name__)


class UtilityWorkflow:
    """Manages the utility agent's workflow using a state graph."""

    def __init__(self, state: UtilityState, comms_manager: UtilityCommsManager):
        self.state = state
        self.comms_manager = comms_manager
        self.llm_provider = get_llm_provider()
        self.graph = self._build_graph()
        self.app = self.graph.compile()
        self._is_running = False
        self._comprehend_task: asyncio.Task | None = None

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(dict)

        # Nodes for the intelligent workflow
        workflow.add_node("comprehend_data", self.comprehend_data)
        workflow.add_node("decide_on_action", self.decide_on_action)
        workflow.add_node("execute_action", self.execute_action)

        # The intelligent workflow starts with comprehending data
        workflow.set_entry_point("comprehend_data")

        # Edges for the intelligent workflow
        workflow.add_edge("comprehend_data", "decide_on_action")
        workflow.add_edge("decide_on_action", "execute_action")
        workflow.add_edge("execute_action", END)

        return workflow

    async def register_der(self, payload: "RegisterDERPayload"):
        """Handles the logic for registering a new DER. (Not part of the graph)"""
        agent_id = payload.id
        logger.info(f"WORKFLOW: Processing registration for agent {agent_id}")
        if agent_id not in self.state.registered_ders:
            self.state.registered_ders[agent_id] = DERStatus(
                id=agent_id,
                type=payload.type,
                api_endpoint=str(payload.api_endpoint),
            )
            logger.info(f"Successfully processed registration for {agent_id}")
        else:
            logger.warning(f"Agent {agent_id} is already registered. Ignoring.")

    async def process_heartbeat(self, payload: "HeartbeatPayload"):
        """Handles the logic for a DER heartbeat. (Not part of the graph)"""
        agent_id = payload.id
        der = self.state.registered_ders.get(agent_id)
        if der:
            der.status = "online"
            der.last_heartbeat = datetime.now()
            logger.debug(f"WORKFLOW: Processed heartbeat for agent {agent_id}")
        else:
            logger.warning(f"WORKFLOW: Heartbeat from unknown agent: {agent_id}")

    async def comprehend_data(self, state: dict) -> dict:
        agent_id = state.get("agent_id")
        sunspec_data = state.get("sunspec_data")
        if not all([agent_id, sunspec_data]):
             logger.error("NODE: Missing agent_id or sunspec_data for comprehension.")
             return {}

        logger.info(f"NODE: Comprehending data for {agent_id}")
        
        # This is where the "belief" is updated
        if agent_id in self.state.registered_ders:
            # The sunspec_data coming in is a Pydantic model, but the graph needs a dict
            if isinstance(sunspec_data, SunSpecData):
                self.state.registered_ders[agent_id].sunspec_data = sunspec_data
                sunspec_data_dict = sunspec_data.dict()
            else: # If it's already a dict (from a previous node)
                self.state.registered_ders[agent_id].sunspec_data = SunSpecData(**sunspec_data)
                sunspec_data_dict = sunspec_data
        else:
            logger.warning(f"Agent {agent_id} not found in state. Cannot update beliefs.")
            sunspec_data_dict = {} if not isinstance(sunspec_data, dict) else sunspec_data

        return {"agent_id": agent_id, "sunspec_data": sunspec_data_dict}

    async def decide_on_action(self, state: dict) -> dict:
        """Analyzes data using an LLM and decides on the next action."""
        agent_id = state.get("agent_id")
        sunspec_data = state.get("sunspec_data")
        if not all([agent_id, sunspec_data]):
            logger.warning("NODE: Missing data for decision.")
            return {"agent_id": agent_id, "decision": "do_nothing"}

        logger.info(f"NODE: Making decision for agent {agent_id}")

        prompt = self._create_decision_prompt(sunspec_data)
        
        try:
            raw_decision = await self.llm_provider.generate(prompt)
            # The output is expected to be a JSON string, so we parse it
            decision_data = json.loads(raw_decision)
            logger.info(f"LLM Decision for {agent_id}: {decision_data}")
            # The entire decision object is passed in the state
            return {"agent_id": agent_id, "decision": decision_data, "sunspec_data": sunspec_data}
        except Exception as e:
            logger.error(f"Error during LLM decision making or parsing: {e}")
            # Fallback to a safe default
            return {"agent_id": agent_id, "decision": {"action": "do_nothing"}, "sunspec_data": sunspec_data}
            
    def _create_decision_prompt(self, sunspec_data: dict) -> str:
        """Creates a prompt for the LLM to decide on an action."""
        return textwrap.dedent(f"""
            You are an autonomous grid operations analyst. Your task is to analyze real-time
            data from a solar DER and decide on the appropriate control action.

            **DER Data:**
            - Nameplate Power: {sunspec_data.get('nameplate_power')} W
            - Inverter Status: {sunspec_data.get('inverter_status')}
            - AC Power Output: {sunspec_data.get('ac_power')} W
            - Fault Message: {sunspec_data.get('fault_message')}

            **Analysis and Action:**
            1.  **If `inverter_status` is 'FAULT'**:
                - A curtailment is necessary to safely manage the asset.
                - Calculate `curtailment_kw` by taking 50% of the `nameplate_power` and converting it to kW (divide by 1000).
                - The `duration_minutes` should be 10 minutes to allow the system to stabilize.
                - Your action is `curtail`.
            2.  **If `inverter_status` is 'NORMAL' or 'STANDBY'**:
                - No intervention is needed.
                - Your action is `do_nothing`.

            **Output Format:**
            You MUST respond with a single, valid JSON object containing your decision.
            Do not include any other text, just the JSON.

            Example for a fault (assuming 5000W Nameplate Power):
            {{
              "action": "curtail",
              "parameters": {{
                "curtailment_kw": 2.5,
                "duration_minutes": 10
              }}
            }}

            Example for normal operation:
            {{
              "action": "do_nothing"
            }}
            
            Now, based on the provided DER data, provide your decision as a single JSON object.
        """).strip()

    async def execute_action(self, state: dict) -> dict:
        """Executes the action decided by the LLM."""
        agent_id = state.get("agent_id")
        decision = state.get("decision", {})
        action = decision.get("action")

        if not all([agent_id, action]):
            logger.error("NODE: Missing agent_id or action in decision for execution.")
            return {}

        logger.info(f"NODE: Executing action '{action}' for agent {agent_id}")

        if action == "curtail":
            der_info = self.state.registered_ders.get(agent_id)
            parameters = decision.get("parameters", {})
            curtailment_kw = parameters.get("curtailment_kw")
            duration_minutes = parameters.get("duration_minutes")

            if not all([der_info, isinstance(curtailment_kw, (int, float)), isinstance(duration_minutes, int)]):
                logger.error(f"Could not execute curtailment for {agent_id}: missing DER info or valid parameters.")
                return {"agent_id": agent_id, "action_taken": "curtail_failed_precondition"}

            logger.warning(
                f"ACTION: Issuing dynamic curtailment to {agent_id} at {der_info.api_endpoint}. "
                f"Curtailment: {curtailment_kw} kW, Duration: {duration_minutes} min."
            )
            
            command = CurtailmentCommand(
                command_id=str(uuid.uuid4()),
                agent_id=agent_id,
                curtailment_kw=curtailment_kw,
                duration_minutes=duration_minutes
            )

            try:
                success = await self.comms_manager.send_curtailment_command(
                    command, der_info.api_endpoint
                )
                if success:
                    self.state.active_commands[agent_id] = command
                    logger.info(f"Successfully sent curtailment command {command.command_id} to {agent_id}")
                else:
                    logger.error(f"Failed to send curtailment command to {agent_id}.")
            except Exception as e:
                logger.error(f"Exception sending curtailment command to {agent_id}: {e}")

        return {"agent_id": agent_id, "action_taken": action}

    async def _comprehension_loop(self, interval_seconds: int = 15):
        """The main loop for polling DER status."""
        while self._is_running:
            logger.debug("Comprehension loop running...")
            if not self.state.registered_ders:
                logger.debug("No registered DERs to poll.")
            else:
                for agent_id, der in self.state.registered_ders.copy().items():
                    logger.debug(f"Polling SunSpec data for agent: {agent_id}")
                    try:
                        sunspec_data = await self.comms_manager.get_sunspec_data(der.api_endpoint)
                        if sunspec_data:
                            # Pass the polled data directly to the compiled graph app
                            await self.app.ainvoke({
                                "agent_id": agent_id,
                                "sunspec_data": sunspec_data
                            })

                    except Exception as e:
                        logger.error(f"Error during comprehension loop for {agent_id}: {e}")
            
            await asyncio.sleep(interval_seconds)

    def start_comprehension_loop(self, interval_seconds: int = 15) -> asyncio.Task:
        """Starts the background task that periodically polls DERs."""
        if not self._is_running:
            self._is_running = True
            self._comprehend_task = asyncio.create_task(self._comprehension_loop(interval_seconds))
            logger.info(f"Starting comprehension loop to poll DERs every {interval_seconds} seconds.")
        return self._comprehend_task

    def stop(self):
        """Stops any running background tasks managed by the workflow."""
        if self._is_running:
            self._is_running = False
            if self._comprehend_task:
                self._comprehend_task.cancel()
                logger.info("Comprehension loop task cancelled.")