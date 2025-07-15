"""
Workflow nodes for the Utility Agent.

Each function in this file represents a node in the LangGraph workflow.
These nodes are responsible for the core business logic of the agent, such as
processing incoming events, making decisions, and initiating outbound communication.

Nodes are designed to be modular and testable. They receive the current state,
perform an action, and return a dictionary representing the updated state.
"""
import logging
import uuid
from typing import Dict, Any, TYPE_CHECKING

from utility_agent.comms import UtilityCommsManager, CommunicationError
from utility_agent.api.models import (
    RegisterDERPayload,
    HeartbeatPayload,
    AckPayload,
    CurtailmentCommand,
    RegisteredDER,
    UtilityState,
)

if TYPE_CHECKING:
    from .state import UtilityState


logger = logging.getLogger(__name__)

def process_der_registration(state: "UtilityState", payload: RegisterDERPayload) -> Dict[str, Any]:
    """
    Processes a DER registration event.
    Updates the state with the new agent's details.
    """
    logger.info(f"NODE: Processing registration for agent {payload.agent_id}")
    
    if payload.agent_id in state.registered_ders:
        logger.info(f"Agent {payload.agent_id} is already registered. Updating details.")
    
    new_der = RegisteredDER(
        id=payload.agent_id,
        type=payload.agent_type,
        api_endpoint=payload.api_endpoint,
        status="online" # Assume online upon registration
    )
    
    updated_ders = state.registered_ders.copy()
    updated_ders[payload.agent_id] = new_der
    
    return {"registered_ders": updated_ders}

def process_heartbeat(state: "UtilityState", payload: HeartbeatPayload) -> Dict[str, Any]:
    """
    Processes a heartbeat event.
    Updates the agent's status and last heartbeat timestamp.
    """
    logger.debug(f"NODE: Processing heartbeat for agent {payload.agent_id}")
    if payload.agent_id not in state.registered_ders:
        logger.error(f"Received heartbeat from unknown agent {payload.agent_id}")
        return {} # No state change

    updated_ders = state.registered_ders.copy()
    der = updated_ders[payload.agent_id]
    der.status = "online"
    der.last_heartbeat = payload.timestamp
    
    return {"registered_ders": updated_ders}

def process_acknowledgement(state: "UtilityState", payload: AckPayload) -> Dict[str, Any]:
    """
    Processes an acknowledgement for a command.
    """
    command_id = payload.command_id
    logger.info(f"NODE: Processing ACK for command {command_id} from {payload.agent_id} with status '{payload.status}'")

    if command_id not in state.active_commands:
        logger.warning(f"Received ACK for unknown or already completed command {command_id}")
        return {}

    # Remove the command from the active list
    updated_commands = state.active_commands.copy()
    del updated_commands[command_id]
    
    logger.info(f"Command {command_id} acknowledged and removed from active list.")
    
    # In a real workflow, you might have different logic for success/failure
    if payload.status == "failure":
        logger.error(f"Agent {payload.agent_id} failed to execute command {command_id}: {payload.message}")
        new_alerts = state.alerts + [f"Command {command_id} failed on agent {payload.agent_id}"]
        return {"active_commands": updated_commands, "alerts": new_alerts}
        
    return {"active_commands": updated_commands}

async def issue_curtailment_command(
    state: "UtilityState", 
    comms_manager: "UtilityCommsManager",
    command: CurtailmentCommand
) -> Dict[str, Any]:
    """
    Looks up a registered agent and sends it a curtailment command.
    This node is triggered by the API.
    """
    logger.info(f"NODE: Issuing curtailment command {command.command_id} to agent {command.agent_id}")
    
    # 1. Find the target agent in the state
    target_agent = state.registered_ders.get(command.agent_id)
    if not target_agent:
        logger.error(f"Cannot issue command: Agent {command.agent_id} not found.")
        return {}

    # 2. Use the comms manager to send the command
    try:
        # Corrected argument order: command object first, then URL
        await comms_manager.send_curtailment_command(command, target_agent.api_endpoint)
        logger.info(f"Successfully sent command {command.command_id} to {target_agent.api_endpoint}")
        
        # 3. Update state to track the active command
        updated_commands = state.active_commands.copy()
        updated_commands[command.command_id] = command
        return {"active_commands": updated_commands}

    except CommunicationError as e:
        logger.error(f"Failed to send command {command.command_id}: {e}")
        # Optionally, add an alert for communication failure
        new_alerts = state.alerts + [f"Failed to communicate with agent {command.agent_id} for command {command.command_id}"]
        return {"alerts": new_alerts}
