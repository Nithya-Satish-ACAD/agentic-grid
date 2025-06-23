"""
API package for Solar Agent.

This package contains FastAPI application and route definitions.
"""

from .main import create_app, get_app
from .routes import router
from .dependencies import get_config, verify_api_key, get_correlation_id

__all__ = ['create_app', 'get_app', 'router', 'get_config', 'verify_api_key', 'get_correlation_id'] 