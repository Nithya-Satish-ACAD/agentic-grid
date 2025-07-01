"""Pydantic models for FastAPI request/response validation."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from solar_agent.core.models import (
    AgentMode,
    CurtailmentStatus,
    AlertType,
    SolarData,
    FaultStatus,
)


class CurtailmentRequest(BaseModel):
    """Request model for curtailment commands."""
    target_output_kw: float = Field(..., ge=0, description="Target output limit in kW")
    duration_minutes: Optional[int] = Field(None, ge=0, description="Duration in minutes")
    start_time: Optional[datetime] = Field(None, description="When to start curtailment")
    end_time: Optional[datetime] = Field(None, description="When to end curtailment")
    priority: int = Field(default=1, ge=1, le=10, description="Command priority (1=highest)")
    reason: Optional[str] = Field(None, description="Reason for curtailment")


class StatusResponse(BaseModel):
    """Response model for agent status."""
    agent_id: str
    timestamp: datetime
    mode: AgentMode
    is_online: bool
    current_output_kw: float
    capacity_kw: float
    utilization_percent: float
    uptime_seconds: int
    last_communication: datetime
    
    # Workflow state
    workflow_step: str
    workflow_iteration: int
    
    # Current data
    latest_solar_data: Optional[SolarData] = None
    
    # Operational state
    active_curtailment: Optional[Dict[str, Any]] = None
    active_faults_count: int
    critical_faults_count: int
    maintenance_mode: bool
    
    # Human-in-the-loop
    pending_approval: bool
    approval_context: Optional[Dict[str, Any]] = None
    
    # Performance metrics
    error_count: int
    communication_failures: int


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(default="healthy", description="Overall health status")
    timestamp: datetime
    agent_id: str
    version: str
    uptime_seconds: int
    mode: AgentMode
    
    components: Dict[str, str] = Field(default_factory=dict, description="Component health status")
    
    # Detailed health info
    adapter_status: str
    workflow_status: str
    api_status: str = Field(default="healthy")
    
    # Error information
    last_error: Optional[str] = None
    error_count: int = Field(default=0)


class AlertRequest(BaseModel):
    """Request model for sending alerts."""
    alert_type: AlertType
    severity: str = Field(..., description="Alert severity level")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional alert data")
    requires_response: bool = Field(default=False, description="Whether alert requires response")


class HumanApprovalRequest(BaseModel):
    """Request model for human-in-the-loop approval."""
    decision: str = Field(..., description="Approval decision (approved/rejected)")
    comments: Optional[str] = Field(None, description="Optional comments")
    override_reason: Optional[str] = Field(None, description="Reason for override if applicable")


class WorkflowInterruptRequest(BaseModel):
    """Request model for workflow interruption."""
    interrupt_type: str = Field(..., description="Type of interrupt")
    context: Dict[str, Any] = Field(..., description="Interrupt context data")
    timeout_minutes: int = Field(default=5, description="Timeout for interrupt")


class ConfigUpdateRequest(BaseModel):
    """Request model for configuration updates."""
    config_section: str = Field(..., description="Configuration section to update")
    updates: Dict[str, Any] = Field(..., description="Configuration updates")
    apply_immediately: bool = Field(default=True, description="Apply changes immediately")


class ErrorResponse(BaseModel):
    """Response model for API errors."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")


class SuccessResponse(BaseModel):
    """Generic success response model."""
    success: bool = Field(default=True)
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FaultStatusResponse(BaseModel):
    """Response model for fault status."""
    agent_id: str
    timestamp: datetime
    total_faults: int
    critical_faults: int
    faults: List[FaultStatus]
    fault_mode: bool


class PerformanceMetrics(BaseModel):
    """Response model for performance metrics."""
    agent_id: str
    timestamp: datetime
    uptime_seconds: int
    
    # Generation metrics
    total_energy_generated_kwh: float
    average_output_kw: float
    peak_output_kw: float
    efficiency_average: float
    
    # Operational metrics
    curtailments_applied: int
    alerts_sent: int
    faults_detected: int
    
    # Availability metrics
    availability_percent: float
    communication_uptime_percent: float
    
    # Recent performance
    last_24h_generation_kwh: float
    last_24h_availability_percent: float


class LogEntry(BaseModel):
    """Model for log entries."""
    timestamp: datetime
    level: str
    logger: str
    message: str
    extra: Optional[Dict[str, Any]] = None


class LogsResponse(BaseModel):
    """Response model for log retrieval."""
    logs: List[LogEntry]
    total_count: int
    page: int
    page_size: int
    has_more: bool


class AdapterInfoResponse(BaseModel):
    """Response model for adapter information."""
    adapter_type: str
    is_connected: bool
    device_info: Dict[str, Any]
    capabilities: Dict[str, Any]
    last_read_timestamp: Optional[datetime] = None
    error_count: int = Field(default=0)
    last_error: Optional[str] = None 