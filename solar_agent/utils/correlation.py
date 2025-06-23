"""
Correlation ID utilities for Solar Agent.

This module provides utilities for generating and propagating correlation IDs
across async context and HTTP headers.
See backend-structure.md for detailed specification.
"""

import uuid
import asyncio
from typing import Optional
from contextvars import ContextVar

# Context variable for correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


def generate_correlation_id() -> str:
    """
    Generate a new correlation ID.
    
    Returns:
        Unique correlation ID string
    """
    return str(uuid.uuid4())


def get_current_correlation_id() -> Optional[str]:
    """
    Get the current correlation ID from context.
    
    Returns:
        Current correlation ID or None
    """
    return correlation_id_var.get()


def set_correlation_id(correlation_id: str) -> None:
    """
    Set correlation ID in current context.
    
    Args:
        correlation_id: Correlation ID to set
    """
    correlation_id_var.set(correlation_id)


def clear_correlation_id() -> None:
    """Clear correlation ID from current context."""
    correlation_id_var.set(None)


class CorrelationContext:
    """Context manager for correlation ID handling."""
    
    def __init__(self, correlation_id: Optional[str] = None):
        """
        Initialize correlation context.
        
        Args:
            correlation_id: Correlation ID to use (generates new one if None)
        """
        self.correlation_id = correlation_id or generate_correlation_id()
        self.previous_id: Optional[str] = None
        
    async def __aenter__(self):
        """Enter async context with correlation ID."""
        self.previous_id = get_current_correlation_id()
        set_correlation_id(self.correlation_id)
        return self.correlation_id
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context and restore previous correlation ID."""
        if self.previous_id is not None:
            set_correlation_id(self.previous_id)
        else:
            clear_correlation_id()


def extract_correlation_id_from_headers(headers: dict) -> Optional[str]:
    """
    Extract correlation ID from HTTP headers.
    
    Args:
        headers: HTTP headers dictionary
        
    Returns:
        Correlation ID from headers or None
    """
    # Check common header names for correlation ID
    header_names = [
        'X-Correlation-ID',
        'X-Request-ID',
        'X-Trace-ID',
        'Correlation-ID',
        'Request-ID'
    ]
    
    for header_name in header_names:
        if header_name in headers:
            return headers[header_name]
            
    return None


def add_correlation_id_to_headers(headers: dict, correlation_id: Optional[str] = None) -> dict:
    """
    Add correlation ID to HTTP headers.
    
    Args:
        headers: HTTP headers dictionary
        correlation_id: Correlation ID to add (uses current if None)
        
    Returns:
        Updated headers dictionary
    """
    if correlation_id is None:
        correlation_id = get_current_correlation_id()
        
    if correlation_id:
        headers['X-Correlation-ID'] = correlation_id
        
    return headers 