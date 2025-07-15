"""Configuration management for Solar Agent."""

import os
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Basic app settings
    app_name: str = "Solar Agent"
    version: str = "1.0.0"
    debug: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8001
    reload: bool = False
    
    # Hardware adapter settings
    adapter_type: str = "mock"  # mock, sunspec
    adapter_host: str = "localhost"
    adapter_port: int = 502
    adapter_unit_id: int = 1
    
    # Agent settings
    agent_id: str = "solar-agent-001"
    location: str = "Default Location"
    capacity_kw: float = 5.0
    efficiency: float = 0.20
    
    # Data generation settings
    data_interval: int = 5  # seconds
    enable_faults: bool = True
    fault_probability: float = 0.1
    weather_effects: bool = True
    
    # LLM Configuration - Simplified to 3 providers
    llm_provider: str = Field(default="openai", description="LLM provider (openai, gemini, ollama)")
    llm_model: str = Field(default="gpt-4o-mini", description="LLM model name")
    llm_api_key: Optional[str] = Field(default=None, description="LLM API key")
    llm_api_base: Optional[str] = Field(default=None, description="Custom API base URL")
    llm_temperature: float = Field(default=0.1, description="LLM generation temperature")
    llm_max_tokens: Optional[int] = Field(default=1000, description="Maximum tokens to generate")
    llm_timeout: int = Field(default=30, description="LLM request timeout")
    
    # OpenAI specific settings
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.1
    openai_max_tokens: int = 1000
    
    # Gemini specific settings
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-flash"
    gemini_temperature: float = 0.1
    gemini_max_tokens: int = 1000
    
    # Ollama specific settings (local models)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_temperature: float = 0.1
    ollama_max_tokens: int = 1000

    # Database settings
    database_url: str = "sqlite:///./solar_agent.db"
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Security settings
    api_key: Optional[str] = None
    cors_origins: str = "*"
    
    # External services
    utility_agent_url: str = "http://localhost:8000"
    mcp_server_url: Optional[str] = None
    weather_api_key: Optional[str] = None
    
    AGENT_ID: str = "solar-agent-1"
    USE_MOCK_ADAPTER: bool = True
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration for the selected provider.
        
        Returns:
            Dictionary with LLM configuration
        """
        provider = self.llm_provider.lower()
        
        # Base configuration
        config = {
            "provider": provider,
            "temperature": self.llm_temperature,
            "max_tokens": self.llm_max_tokens,
            "timeout": self.llm_timeout,
        }
        
        # Provider-specific configuration
        if provider in ["openai"]:
            config.update({
                "model": self.llm_model or self.openai_model,
                "api_key": self.llm_api_key or self.openai_api_key,
                "api_base": self.llm_api_base,
            })
        elif provider in ["gemini", "google"]:
            config.update({
                "model": self.llm_model or self.gemini_model,
                "api_key": self.llm_api_key or self.gemini_api_key,
                "api_base": self.llm_api_base,
            })
        elif provider == "ollama":
            config.update({
                "model": self.llm_model or self.ollama_model,
                "api_base": self.llm_api_base or self.ollama_base_url,
            })
        else:
            # Generic configuration
            config.update({
                "model": self.llm_model,
                "api_key": self.llm_api_key,
                "api_base": self.llm_api_base,
            })
        
        return config


# Global settings instance
settings = Settings()

def setup_logging():
    """Sets up the logging for the application."""
    import logging
    import sys

    log_level = settings.log_level.upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    logging.getLogger("httpx").setLevel("WARNING")
    logging.getLogger("uvicorn").setLevel("WARNING")
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level {log_level}") 