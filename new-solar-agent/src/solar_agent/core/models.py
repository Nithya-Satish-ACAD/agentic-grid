"""Core data models for Solar Agent."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
import uuid


class AgentMode(str, Enum):
    """Agent operational modes."""
    NORMAL = "normal"
    MAINTENANCE = "maintenance" 
    FAULT = "fault"
    OFFLINE = "offline"
    CURTAILED = "curtailed"


class AlertType(str, Enum):
    """Types of alerts that can be raised."""
    UNDERPERFORMANCE = "underperformance"
    FAULT = "fault"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    CURTAILMENT_FAILED = "curtailment_failed"


class CurtailmentStatus(str, Enum):
    """Status of curtailment operations."""
    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"
    EXPIRED = "expired"


class SolarData(BaseModel):
    """Solar panel data reading."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    current_output_kw: float = Field(..., ge=0, description="Current power output in kW")
    voltage_v: float = Field(..., ge=0, description="DC voltage in volts")
    current_a: float = Field(..., ge=0, description="DC current in amperes")
    efficiency: float = Field(..., ge=0, le=1, description="Panel efficiency (0-1)")
    temperature_c: float = Field(..., description="Panel temperature in Celsius")
    irradiance_w_m2: float = Field(..., ge=0, description="Solar irradiance in W/m²")
    
    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GenerationForecast(BaseModel):
    """Generation forecast for a specific time period."""
    forecast_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    forecast_period_start: datetime
    forecast_period_end: datetime
    predicted_output_kw: float = Field(..., ge=0, description="Predicted power output")
    confidence_level: float = Field(..., ge=0, le=1, description="Confidence in forecast")
    
    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FaultStatus(BaseModel):
    """Hardware fault status information."""
    fault_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    fault_type: str = Field(..., description="Type of fault detected")
    severity: str = Field(..., description="Fault severity level")
    description: str = Field(..., description="Human-readable fault description")
    is_critical: bool = Field(default=False, description="Whether fault is critical")
    
    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CurtailmentCommand(BaseModel):
    """Curtailment command from Utility Agent."""
    command_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    target_output_kw: float = Field(..., ge=0, description="Target output level in kW")
    duration_minutes: Optional[int] = Field(None, ge=0, description="Duration of curtailment")
    status: CurtailmentStatus = Field(default=CurtailmentStatus.PENDING)
    
    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AgentStatus(BaseModel):
    """Current status of the Solar Agent."""
    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    mode: AgentMode = Field(default=AgentMode.NORMAL)
    is_online: bool = Field(default=True)
    current_output_kw: float = Field(..., ge=0)
    capacity_kw: float = Field(..., ge=0)
    
    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 

"""Core Pydantic models for the Solar Agent's internal state and data structures."""
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

class SunSpecInverterStatus(str, Enum):
    """Enumeration for the operational state of a SunSpec-compliant inverter."""
    NORMAL = "NORMAL"
    FAULT = "FAULT"
    SHUTDOWN = "SHUTDOWN"
    STANDBY = "STANDBY"

class SunSpecData(BaseModel):
    """
    A simplified Pydantic model representing mock data from a SunSpec-compliant device.
    This model forms the 'Beliefs' of the Solar Agent about its environment.
    """
    nameplate_power: float = Field(
        ...,
        description="The maximum rated AC power output of the inverter in Watts.",
        examples=[5000.0]
    )
    inverter_status: SunSpecInverterStatus = Field(
        SunSpecInverterStatus.NORMAL,
        description="The current operational status of the inverter."
    )
    ac_power: float = Field(
        ...,
        description="Current AC power output in Watts.",
        examples=[4500.0]
    )
    daily_yield: float = Field(
        ...,
        description="Cumulative energy produced today in kWh.",
        examples=[15.2]
    )
    dc_voltage: float = Field(
        ...,
        description="Current DC voltage from the solar array.",
        examples=[380.5]
    )
    irradiance: float = Field(
        ...,
        description="Current solar irradiance in W/m^2.",
        examples=[850.0]
    )
    ambient_temp: float = Field(
        ...,
        description="Ambient temperature in Celsius.",
        examples=[25.5]
    )
    fault_message: Optional[str] = Field(
        None,
        description="A human-readable fault message if the inverter is in a FAULT state."
    )