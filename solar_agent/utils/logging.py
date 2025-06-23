"""
Structured logging configuration for Solar Agent.

This module configures structured logging with correlation ID integration.
See backend-structure.md for detailed specification.
"""

import sys
import structlog
from typing import Optional
from contextvars import ContextVar
from ..models.config import SolarAgentConfig

# Context variable for correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

# Global configuration for logging context
_logging_config: Optional[SolarAgentConfig] = None


def configure_logging(config: SolarAgentConfig) -> None:
    """
    Configure structured logging with configuration context.
    
    Args:
        config: Solar Agent configuration
    """
    global _logging_config
    _logging_config = config
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            _add_context_fields,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    import logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, config.log_level.upper())
    )


def _add_context_fields(logger, method_name, event_dict):
    """Add correlation ID and configuration context to log entries."""
    # Add correlation ID
    correlation_id = correlation_id_var.get()
    if correlation_id:
        event_dict['correlation_id'] = correlation_id
    
    # Add configuration context if available
    if _logging_config:
        event_dict['site_id'] = _logging_config.site_id
        event_dict['agent_id'] = _logging_config.agent_id
    
    return event_dict


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance with context binding.
    
    Args:
        name: Logger name
        
    Returns:
        Structured logger instance with context
    """
    logger = structlog.get_logger(name)
    
    # Bind configuration context if available
    if _logging_config:
        logger = logger.bind(
            site_id=_logging_config.site_id,
            agent_id=_logging_config.agent_id
        )
    
    return logger


def set_correlation_id(correlation_id: str) -> None:
    """
    Set correlation ID for current context.
    
    Args:
        correlation_id: Correlation ID string
    """
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """
    Get current correlation ID.
    
    Returns:
        Current correlation ID or None
    """
    return correlation_id_var.get()


def clear_correlation_id() -> None:
    """Clear current correlation ID."""
    correlation_id_var.set(None) 