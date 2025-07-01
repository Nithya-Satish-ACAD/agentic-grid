"""Custom exceptions for Solar Agent."""

from typing import Optional, Dict, Any


class SolarAgentException(Exception):
    """Base exception for Solar Agent."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/API responses."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
        }


class AdapterException(SolarAgentException):
    """Exception raised by hardware adapters."""
    
    def __init__(
        self, 
        message: str, 
        adapter_type: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.adapter_type = adapter_type
        super().__init__(message, error_code, details)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        result = super().to_dict()
        result["adapter_type"] = self.adapter_type
        return result


class WorkflowException(SolarAgentException):
    """Exception raised during LangGraph workflow execution."""
    
    def __init__(
        self, 
        message: str,
        node_name: Optional[str] = None,
        workflow_state: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.node_name = node_name
        self.workflow_state = workflow_state
        super().__init__(message, error_code, details)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        result = super().to_dict()
        result["node_name"] = self.node_name
        result["workflow_state"] = self.workflow_state
        return result


class CurtailmentException(SolarAgentException):
    """Exception raised during curtailment operations."""
    
    def __init__(
        self, 
        message: str,
        command_id: Optional[str] = None,
        target_output: Optional[float] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.command_id = command_id
        self.target_output = target_output
        super().__init__(message, error_code, details)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        result = super().to_dict()
        result["command_id"] = self.command_id
        result["target_output"] = self.target_output
        return result


class ForecastingException(SolarAgentException):
    """Exception raised during forecasting operations."""
    
    def __init__(
        self, 
        message: str,
        model_version: Optional[str] = None,
        forecast_period: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.model_version = model_version
        self.forecast_period = forecast_period
        super().__init__(message, error_code, details)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        result = super().to_dict()
        result["model_version"] = self.model_version
        result["forecast_period"] = self.forecast_period
        return result


class AlertException(SolarAgentException):
    """Exception raised during alert operations."""
    
    def __init__(
        self, 
        message: str,
        alert_type: Optional[str] = None,
        retry_count: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.alert_type = alert_type
        self.retry_count = retry_count
        super().__init__(message, error_code, details)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        result = super().to_dict()
        result["alert_type"] = self.alert_type
        result["retry_count"] = self.retry_count
        return result


class MCPException(SolarAgentException):
    """Exception raised during MCP client operations."""
    
    def __init__(
        self, 
        message: str,
        server_url: Optional[str] = None,
        operation: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.server_url = server_url
        self.operation = operation
        super().__init__(message, error_code, details)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        result = super().to_dict()
        result["server_url"] = self.server_url
        result["operation"] = self.operation
        return result


class HumanInTheLoopException(SolarAgentException):
    """Exception raised during human-in-the-loop operations."""
    
    def __init__(
        self, 
        message: str,
        approval_context: Optional[Dict[str, Any]] = None,
        timeout_reached: bool = False,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.approval_context = approval_context
        self.timeout_reached = timeout_reached
        super().__init__(message, error_code, details)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        result = super().to_dict()
        result["approval_context"] = self.approval_context
        result["timeout_reached"] = self.timeout_reached
        return result 