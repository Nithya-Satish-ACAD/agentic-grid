"""LangGraph workflow state definition for Solar Agent."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from solar_agent.core.models import (
    AgentMode,
    SolarData,
    GenerationForecast,
    CurtailmentCommand,
    FaultStatus,
)


class WorkflowState(BaseModel):
    """State object for LangGraph workflow."""
    
    # Agent identification
    agent_id: str
    
    # Current operational mode  
    current_mode: AgentMode = AgentMode.NORMAL
    
    # Data readings
    latest_solar_data: Optional[SolarData] = None
    current_forecast: Optional[GenerationForecast] = None
    
    # Operational state
    active_curtailment: Optional[CurtailmentCommand] = None
    active_faults: List[FaultStatus] = Field(default_factory=list)
    maintenance_mode: bool = Field(default=False)
    
    # Workflow control
    workflow_step: str = Field(default="read_solar_data")
    workflow_iteration: int = Field(default=0)
    last_update: datetime = Field(default_factory=datetime.utcnow)
    
    # Human-in-the-loop
    pending_approval: bool = Field(default=False)
    approval_context: Optional[Dict[str, Any]] = None
    
    # Error handling
    error_count: int = Field(default=0)
    last_error: Optional[str] = None
    
    # Performance tracking
    uptime_start: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def update_timestamp(self) -> None:
        """Update the last update timestamp."""
        self.last_update = datetime.utcnow()
    
    def set_step(self, step: str) -> None:
        """Set current workflow step."""
        self.workflow_step = step
        self.update_timestamp() 