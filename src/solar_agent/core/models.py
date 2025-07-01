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


class WorkflowState(BaseModel):
    """State object for LangGraph workflow."""
    agent_id: str
    current_mode: AgentMode = AgentMode.NORMAL
    latest_solar_data: Optional[SolarData] = None
    current_forecast: Optional[GenerationForecast] = None
    active_curtailment: Optional[CurtailmentCommand] = None
    active_faults: List[FaultStatus] = Field(default_factory=list)
    workflow_step: str = Field(default="read_solar_data")
    last_update: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 