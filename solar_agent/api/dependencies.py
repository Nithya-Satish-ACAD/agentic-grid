"""
API dependencies for Solar Agent.

This module provides dependency injection for authentication,
configuration, and correlation ID handling.
See backend-structure.md for detailed specification.
"""

from typing import Optional
from fastapi import Depends, HTTPException, Header, Request
from ..models.config import get_config
from ..utils.correlation import extract_correlation_id_from_headers, set_correlation_id


def verify_api_key(
    x_api_key: Optional[str] = Header(None),
    config = Depends(get_config)
) -> str:
    """
    Verify API key authentication.
    
    Args:
        x_api_key: API key from header
        config: Application configuration
        
    Returns:
        Verified API key
        
    Raises:
        HTTPException: If API key is invalid
    """
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
        
    if x_api_key != config.api_key_solar:
        raise HTTPException(status_code=401, detail="Invalid API key")
        
    return x_api_key


def get_correlation_id(
    request: Request,
    x_correlation_id: Optional[str] = Header(None)
) -> Optional[str]:
    """
    Extract and set correlation ID from request.
    
    Args:
        request: FastAPI request object
        x_correlation_id: Correlation ID from header
        
    Returns:
        Correlation ID string
    """
    # Try header first, then extract from request headers
    correlation_id = x_correlation_id or extract_correlation_id_from_headers(dict(request.headers))
    
    if correlation_id:
        set_correlation_id(correlation_id)
        
    return correlation_id 