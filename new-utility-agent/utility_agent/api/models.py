"""
Pydantic models for the Utility Agent API, designed for event-driven communication.

These models define the data structures for HTTP POST requests between agents.
They are designed to be easily adaptable to a full A2A communication protocol in the future.
Each model corresponds to a specific "agent event" (e.g., registration, heartbeat, curtailment).
"""
import logging
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, AnyHttpUrl
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

# ==============================================================================
# SunSpec Models (for storing polled data)
# ==============================================================================

class SunSpecInverterStatus(str, Enum):
    """Enumeration for the operational state of a SunSpec-compliant inverter."""
    NORMAL = "NORMAL"
    FAULT = "FAULT"
    SHUTDOWN = "SHUTDOWN"
    STANDBY = "STANDBY"

class SunSpecData(BaseModel):
    """
    A simplified Pydantic model representing mock data from a SunSpec-compliant device.
    This model is used by the Utility Agent to understand the state of a DER.
    """
    nameplate_power: float = Field(
        ...,
        description="The maximum rated AC power output of the inverter in Watts.",
        examples=[5000.0]
    )
    inverter_status: SunSpecInverterStatus
    ac_power: float
    daily_yield: float
    dc_voltage: float
    irradiance: float
    ambient_temp: float
    fault_message: Optional[str] = None

# ==============================================================================
# Core Agent-to-Agent Event Models
# ==============================================================================

class RegisterDERPayload(BaseModel):
    """Payload for a DER to register."""

    id: str = Field(..., description="Unique identifier for the agent.")
    type: str = Field(..., description="Type of the DER agent (e.g., 'solar', 'battery').")
    api_endpoint: AnyHttpUrl = Field(
        ..., description="The base URL for the agent's API."
    )


class HeartbeatPayload(BaseModel):
    """Payload for a DER to send a heartbeat."""

    id: str = Field(..., description="Unique identifier for the agent.")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="The timestamp of the heartbeat.",
    )

class StatusUpdatePayload(BaseModel):
    """
    Payload for a Solar Agent to send its detailed operational status.
    Event: 'status_update'
    """
    agent_id: str
    power_output: float = Field(..., description="Current power output in kW")
    availability: float = Field(..., description="Available capacity in kW")
    timestamp: datetime = Field(default_factory=datetime.now)

class CurtailmentCommand(BaseModel):
    """
    Payload for the Utility Agent to command a Solar Agent to curtail power.
    Event: 'curtailment_command'
    """
    command_id: str = Field(..., description="Unique ID for this command")
    agent_id: str = Field(..., description="Identifier of the target agent")
    curtailment_kw: float = Field(..., description="Amount of power to curtail in kW")
    duration_minutes: int = Field(..., description="Duration of the curtailment in minutes")

class AckPayload(BaseModel):
    """
    Generic acknowledgement payload sent in response to a command.
    Event: 'acknowledgement'
    """
    command_id: str = Field(..., description="The ID of the command being acknowledged")
    agent_id: str = Field(..., description="Identifier of the acknowledging agent")
    status: str = Field(..., description="Status of the command execution", examples=["success", "failure"])
    message: Optional[str] = Field(None, description="Optional message providing more details")
    timestamp: datetime = Field(default_factory=datetime.now)


# ==============================================================================
# Beckn/UEI Stub Models (for validation and future upgrade)
# ==============================================================================

class BecknContext(BaseModel):
    """A simplified Beckn context for stub validation."""
    domain: str
    action: str
    message_id: str
    # In a real implementation, add bpp_id, bap_id, transaction_id etc.

# --- Search ---
class BecknSearchRequest(BaseModel):
    """Stub model for a Beckn 'search' request."""
    context: BecknContext
    # The message for 'search' is complex, so we use a dict for the stub.
    message: dict 

class BecknOnSearchResponse(BaseModel):
    """Stub model for a Beckn 'on_search' response."""
    context: BecknContext
    message: dict

# --- Select ---
class BecknSelectRequest(BaseModel):
    context: BecknContext
    message: dict

class BecknOnSelectResponse(BaseModel):
    context: BecknContext
    message: dict

# --- Init ---
class BecknInitRequest(BaseModel):
    context: BecknContext
    message: dict

class BecknOnInitResponse(BaseModel):
    context: BecknContext
    message: dict

# --- Confirm ---
class BecknConfirmRequest(BaseModel):
    context: BecknContext
    message: dict

class BecknOnConfirmResponse(BaseModel):
    context: BecknContext
    message: dict

# --- Status ---
class BecknStatusRequest(BaseModel):
    context: BecknContext
    message: dict

class BecknOnStatusResponse(BaseModel):
    context: BecknContext
    message: dict

# --- Update ---
class BecknUpdateRequest(BaseModel):
    context: BecknContext
    message: dict

class BecknOnUpdateResponse(BaseModel):
    context: BecknContext
    message: dict

# --- Cancel ---
class BecknCancelRequest(BaseModel):
    context: BecknContext
    message: dict

class BecknOnCancelResponse(BaseModel):
    context: BecknContext
    message: dict


# ==============================================================================
# Internal State Models (Not part of the public API)
# ==============================================================================

class DERStatus(BaseModel):
    """Represents the complete status of a registered DER."""
    id: str
    type: str
    api_endpoint: str
    status: str = "offline"
    last_heartbeat: Optional[datetime] = None
    sunspec_data: Optional[SunSpecData] = None


class UtilityState(BaseModel):
    """Represents the overall state of the utility agent."""

    registered_ders: Dict[str, DERStatus] = {}
    active_commands: Dict[str, CurtailmentCommand] = {}
    alerts: List[str] = []

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "registered_ders": {
                        "solar-agent-001": {
                            "id": "solar-agent-001",
                            "type": "solar",
                            "api_endpoint": "http://localhost:8001",
                            "status": "online",
                            "last_heartbeat": "2025-07-15T12:00:00Z",
                            "sunspec_data": {
                                "nameplate_power": 5000.0,
                                "inverter_status": "NORMAL",
                                "ac_power": 5000.0,
                                "daily_yield": 25.5,
                                "dc_voltage": 400.0,
                                "irradiance": 800.0,
                                "ambient_temp": 28.5,
                                "fault_message": None,
                            },
                        }
                    },
                    "active_commands": {},
                    "alerts": [],
                }
            ]
        }
    }

class SimpleAck(BaseModel):
    """A simple acknowledgement response."""
    status: str = "ok"
