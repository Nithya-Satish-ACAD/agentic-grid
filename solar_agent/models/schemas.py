"""
Pydantic models for Solar Agent API payloads.

This module defines the data models for all API requests and responses.
See backend-structure.md for detailed specification.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RegisterPayload(BaseModel):
    """Payload for agent registration."""
    agent_id: str = Field(..., description="Unique agent identifier")
    site_id: str = Field(..., description="Site identifier")
    location: Dict[str, float] = Field(..., description="GPS coordinates {lat, lon}")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")


class StatusPayload(BaseModel):
    """Payload for agent status updates."""
    agent_id: str = Field(..., description="Agent identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(..., description="Current status")
    power_kw: float = Field(..., description="Current power output in kW")
    error_code: Optional[str] = Field(None, description="Error code if applicable")


class ForecastPoint(BaseModel):
    """Single forecast data point."""
    timestamp: datetime = Field(..., description="Forecast timestamp")
    predicted_kw: float = Field(..., description="Predicted power in kW")
    confidence: float = Field(..., description="Forecast confidence (0-1)")


class ForecastPayload(BaseModel):
    """Payload for power forecasts."""
    agent_id: str = Field(..., description="Agent identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    forecast: List[ForecastPoint] = Field(..., description="Forecast data points")
    weather_conditions: Dict[str, Any] = Field(default_factory=dict, description="Weather data used")


class AlertPayload(BaseModel):
    """Payload for anomaly alerts."""
    agent_id: str = Field(..., description="Agent identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    severity: str = Field(..., description="Alert severity: low, medium, high, critical")
    explanation: str = Field(..., description="Anomaly explanation")
    causes: List[str] = Field(default_factory=list, description="Identified causes")
    recommendations: List[str] = Field(default_factory=list, description="Recommended actions")
    actual_power_kw: float = Field(..., description="Actual power reading")
    expected_power_kw: float = Field(..., description="Expected power reading")


class CommandPayload(BaseModel):
    """Payload for inverter commands."""
    command: str = Field(..., description="Command to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Command parameters")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CommandResponse(BaseModel):
    """Response to command execution."""
    success: bool = Field(..., description="Command execution success")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error_code: Optional[str] = Field(None, description="Error code if failed") 