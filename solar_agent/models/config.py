"""
Configuration management for Solar Agent.

This module handles environment variable loading and configuration validation.
See backend-structure.md for detailed specification.
"""

import os
import uuid
import logging
from functools import lru_cache
from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing required values."""
    pass


class SolarAgentConfig(BaseSettings):
    """Configuration for Solar Agent using Pydantic BaseSettings."""
    
    # Site and Agent Identification
    site_id: str = Field(..., description="Site identifier")
    agent_id: str = Field("", description="Agent identifier (auto-generated if not provided)")
    
    # External Service URLs
    utility_url: str = Field(..., description="Utility service URL")
    weather_mcp_url: str = Field(..., description="Weather MCP server URL")
    
    # Authentication
    api_key_solar: str = Field(..., description="Solar API key")
    llm_api_key: Optional[str] = Field(None, description="LLM API key")
    
    # Operational Parameters
    forecast_interval: int = Field(300, description="Forecast interval in seconds")
    anomaly_threshold: float = Field(0.15, description="Anomaly detection threshold")
    reading_history_size: int = Field(100, description="Reading history size")
    
    # Adapter Configuration
    adapter_type: str = Field("simulated", description="Adapter type")
    failure_rate: float = Field(0.0, description="Simulated failure rate")
    failure_duration: int = Field(60, description="Simulated failure duration")
    base_power_kw: float = Field(5.0, description="Base power in kW")
    power_variation: float = Field(2.0, description="Power variation")
    
    # Logging and Monitoring
    log_level: str = Field("INFO", description="Logging level")
    metrics_port: int = Field(8000, description="Metrics port")
    
    # Timeouts
    http_timeout: int = Field(30, description="HTTP timeout in seconds")
    mcp_timeout: int = Field(30, description="MCP timeout in seconds")
    llm_timeout: int = Field(60, description="LLM timeout in seconds")
    
    # Retry Configuration
    max_retries: int = Field(3, description="Maximum retries")
    retry_backoff_factor: float = Field(2.0, description="Retry backoff factor")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator('anomaly_threshold')
    def validate_anomaly_threshold(cls, v):
        """Validate anomaly threshold is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("ANOMALY_THRESHOLD must be between 0.0 and 1.0")
        return v
    
    @validator('failure_rate')
    def validate_failure_rate(cls, v):
        """Validate failure rate is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("FAILURE_RATE must be between 0.0 and 1.0")
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    @validator('agent_id', pre=True, always=True)
    def generate_agent_id_if_missing(cls, v):
        """Generate agent ID if not provided."""
        if not v:
            generated = str(uuid.uuid4())
            logger = logging.getLogger(__name__)
            logger.info(f"Generated AGENT_ID: {generated}")
            return generated
        return v


@lru_cache()
def get_config() -> SolarAgentConfig:
    """
    Get cached configuration instance.
    
    Returns:
        SolarAgentConfig instance
        
    Raises:
        ConfigurationError: If required environment variables are missing or invalid
    """
    try:
        return SolarAgentConfig()
    except Exception as e:
        raise ConfigurationError(f"Configuration error: {e}")


# Legacy method for backward compatibility
def from_env() -> SolarAgentConfig:
    """
    Load configuration from environment variables (legacy method).
    
    Returns:
        SolarAgentConfig instance
    """
    return get_config() 