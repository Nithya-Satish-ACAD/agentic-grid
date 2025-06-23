"""
Unit tests for configuration management.

Tests for environment variable loading, validation, and UUID generation.
"""

import os
import pytest
import uuid
from unittest.mock import patch
from solar_agent.models.config import SolarAgentConfig, get_config, ConfigurationError


class TestSolarAgentConfig:
    """Test cases for SolarAgentConfig."""
    
    @pytest.fixture
    def valid_env_vars(self):
        """Set up valid environment variables for testing."""
        env_vars = {
            'SITE_ID': 'test-site-001',
            'AGENT_ID': 'test-agent-001',
            'UTILITY_URL': 'http://localhost:8001',
            'WEATHER_MCP_URL': 'http://localhost:8002',
            'API_KEY_SOLAR': 'test-api-key',
            'LLM_API_KEY': 'test-llm-key',
            'FORECAST_INTERVAL': '300',
            'ANOMALY_THRESHOLD': '0.15',
            'LOG_LEVEL': 'INFO'
        }
        
        # Set environment variables
        for key, value in env_vars.items():
            os.environ[key] = value
            
        yield env_vars
        
        # Clean up environment variables
        for key in env_vars:
            if key in os.environ:
                del os.environ[key]
    
    def test_load_config_with_all_required_vars(self, valid_env_vars):
        """Test loading configuration with all required environment variables set."""
        config = get_config()
        
        assert config.site_id == 'test-site-001'
        assert config.agent_id == 'test-agent-001'
        assert config.utility_url == 'http://localhost:8001'
        assert config.weather_mcp_url == 'http://localhost:8002'
        assert config.api_key_solar == 'test-api-key'
        assert config.llm_api_key == 'test-llm-key'
        assert config.forecast_interval == 300
        assert config.anomaly_threshold == 0.15
        assert config.log_level == 'INFO'
    
    def test_missing_required_environment_variable(self):
        """Test that missing required environment variable raises exception."""
        # Clear all environment variables
        required_vars = ['SITE_ID', 'UTILITY_URL', 'WEATHER_MCP_URL', 'API_KEY_SOLAR']
        
        for var in required_vars:
            if var in os.environ:
                del os.environ[var]
        
        with pytest.raises(ConfigurationError) as exc_info:
            get_config()
        
        assert "Configuration error" in str(exc_info.value)
    
    def test_agent_id_generation_when_missing(self):
        """Test that AGENT_ID is generated when not provided."""
        # Set required environment variables
        os.environ['SITE_ID'] = 'test-site'
        os.environ['UTILITY_URL'] = 'http://localhost:8001'
        os.environ['WEATHER_MCP_URL'] = 'http://localhost:8002'
        os.environ['API_KEY_SOLAR'] = 'test-key'
        
        # Remove AGENT_ID if it exists
        if 'AGENT_ID' in os.environ:
            del os.environ['AGENT_ID']
        
        config = get_config()
        
        # Verify that agent_id is a valid UUID
        try:
            uuid.UUID(config.agent_id)
        except ValueError:
            pytest.fail(f"Generated agent_id '{config.agent_id}' is not a valid UUID")
    
    def test_invalid_anomaly_threshold_range(self):
        """Test that anomaly threshold outside valid range raises exception."""
        # Set required environment variables
        os.environ['SITE_ID'] = 'test-site'
        os.environ['UTILITY_URL'] = 'http://localhost:8001'
        os.environ['WEATHER_MCP_URL'] = 'http://localhost:8002'
        os.environ['API_KEY_SOLAR'] = 'test-key'
        os.environ['ANOMALY_THRESHOLD'] = '1.5'  # Invalid: > 1.0
        
        with pytest.raises(ConfigurationError) as exc_info:
            get_config()
        
        assert "ANOMALY_THRESHOLD must be between 0.0 and 1.0" in str(exc_info.value)
    
    def test_invalid_log_level(self):
        """Test that invalid log level raises exception."""
        # Set required environment variables
        os.environ['SITE_ID'] = 'test-site'
        os.environ['UTILITY_URL'] = 'http://localhost:8001'
        os.environ['WEATHER_MCP_URL'] = 'http://localhost:8002'
        os.environ['API_KEY_SOLAR'] = 'test-key'
        os.environ['LOG_LEVEL'] = 'INVALID_LEVEL'
        
        with pytest.raises(ConfigurationError) as exc_info:
            get_config()
        
        assert "LOG_LEVEL must be one of" in str(exc_info.value)
    
    def test_default_values(self):
        """Test that default values are used when environment variables are not set."""
        # Set only required environment variables
        os.environ['SITE_ID'] = 'test-site'
        os.environ['UTILITY_URL'] = 'http://localhost:8001'
        os.environ['WEATHER_MCP_URL'] = 'http://localhost:8002'
        os.environ['API_KEY_SOLAR'] = 'test-key'
        
        config = get_config()
        
        # Check default values
        assert config.forecast_interval == 300
        assert config.anomaly_threshold == 0.15
        assert config.reading_history_size == 100
        assert config.log_level == 'INFO'
        assert config.metrics_port == 8000
        assert config.http_timeout == 30
        assert config.mcp_timeout == 30
        assert config.llm_timeout == 60
        assert config.max_retries == 3
        assert config.retry_backoff_factor == 2.0
    
    def test_optional_llm_api_key(self):
        """Test that LLM_API_KEY is optional."""
        # Set required environment variables
        os.environ['SITE_ID'] = 'test-site'
        os.environ['UTILITY_URL'] = 'http://localhost:8001'
        os.environ['WEATHER_MCP_URL'] = 'http://localhost:8002'
        os.environ['API_KEY_SOLAR'] = 'test-key'
        
        # Remove LLM_API_KEY if it exists
        if 'LLM_API_KEY' in os.environ:
            del os.environ['LLM_API_KEY']
        
        config = get_config()
        assert config.llm_api_key is None
    
    def test_config_caching(self):
        """Test that get_config() returns cached instance."""
        # Set required environment variables
        os.environ['SITE_ID'] = 'test-site'
        os.environ['UTILITY_URL'] = 'http://localhost:8001'
        os.environ['WEATHER_MCP_URL'] = 'http://localhost:8002'
        os.environ['API_KEY_SOLAR'] = 'test-key'
        
        config1 = get_config()
        config2 = get_config()
        
        # Should be the same instance due to caching
        assert config1 is config2 