"""
Solar Agent - A robust, modular microservice for solar power monitoring.

This package provides a complete solution for solar power monitoring,
forecasting, and anomaly detection with AI integration.
"""

__version__ = "1.0.0"
__author__ = "Solar Agent Team"
__description__ = "Solar power monitoring and forecasting microservice"

from .models.config import SolarAgentConfig, get_config

__all__ = ['SolarAgentConfig', 'get_config'] 