"""
Pydantic models for the Solar Agent API, designed for event-driven communication.

These models define the data structures for HTTP POST requests between agents.
They are designed to be easily adaptable to a full A2A communication protocol in the future.
Each model corresponds to a specific "agent event" (e.g., registration, heartbeat, curtailment).
"""
import datetime
import uuid
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

# ==============================================================================
# Core Agent-to-Agent Event Models
# (Mirrors the models in the Utility Agent to ensure a common communication protocol)
# ==============================================================================

class RegisterDERPayload(BaseModel):
    """
    Payload for this agent to register itself with the Utility Agent.
    Event: 'der_registration'
    """
    id: str = Field(..., description="Unique identifier for the DER agent")
    type: str = Field(..., description="Type of DER, e.g., 'solar', 'battery'", examples=["solar"])
    api_endpoint: str = Field(..., description="The base URL for this agent's API")


class HeartbeatPayload(BaseModel):
    """
    Payload for this agent to send a heartbeat to the Utility Agent.
    Event: 'heartbeat'
    """
    id: str = Field(..., description="Unique identifier of the sending agent")
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)

class StatusUpdatePayload(BaseModel):
    """
    Payload for this agent to send its detailed operational status.
    Event: 'status_update'
    """
    agent_id: str
    power_output: float = Field(..., description="Current power output in kW")
    availability: float = Field(..., description="Available capacity in kW")
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)

class CurtailmentCommand(BaseModel):
    """
    Payload received from the Utility Agent to command this agent to curtail power.
    Event: 'curtailment_command'
    """
    command_id: str = Field(..., description="Unique ID for this command")
    agent_id: str = Field(..., description="Identifier of the target agent (should be this agent's ID)")
    curtailment_kw: float = Field(..., description="Amount of power to curtail in kW")
    duration_minutes: int = Field(..., description="Duration of the curtailment in minutes")

class AckPayload(BaseModel):
    """
    Generic acknowledgement payload sent in response to a command.
    Event: 'acknowledgement'
    """
    command_id: str = Field(..., description="The ID of the command being acknowledged")
    agent_id: str = Field(..., description="Identifier of this agent")
    status: str = Field(..., description="Status of the command execution", examples=["success", "failure"])
    message: Optional[str] = Field(None, description="Optional message providing more details")
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)


class SimpleAck(BaseModel):
    """A simple acknowledgement response."""
    status: str = "ok"


# ==============================================================================
# Beckn/UEI Stub Models
# ==============================================================================

class BecknContext(BaseModel):
    """
    Represents the context of a Beckn message.
    """
    domain: str = Field("dsep:energy", description="The domain of the transaction")
    country: str = Field("IND", description="Country code (ISO 3166-1 alpha-3)")
    city: str = Field("std:080", description="City code")
    action: str = Field(..., description="The action being performed, e.g., 'search'")
    core_version: str = Field("1.2.0", description="Core specification version")
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for this message")
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)

class BecknSearchRequest(BaseModel):
    """
    Stub model for this agent to send a Beckn 'search' request.
    Event: 'beckn_search'
    """
    context: BecknContext
    message: Dict[str, Any]

class BecknOnSearchResponse(BaseModel):
    """
    Stub model for this agent to receive an 'on_search' response.
    Event: 'beckn_on_search'
    """
    context: BecknContext
    message: Dict[str, Any]


# ==============================================================================
# Internal State Models
# ==============================================================================

class SolarAgentState(BaseModel):
    """Internal model representing the state of the Solar Agent."""
    agent_id: str = "solar-agent-001"
    utility_agent_url: str = "http://localhost:8000"
    is_registered: bool = False
    is_online: bool = True
    power_output_kw: float = 50.0
    availability_kw: float = 50.0
    active_command: Optional[CurtailmentCommand] = None
    last_heartbeat: Optional[datetime.datetime] = None 