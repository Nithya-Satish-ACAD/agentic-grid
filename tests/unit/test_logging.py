"""
Unit tests for structured logging.

Tests for logging configuration, context binding, and JSON output.
"""

import json
import pytest
import logging
from io import StringIO
from unittest.mock import patch
from solar_agent.models.config import SolarAgentConfig
from solar_agent.utils.logging import configure_logging, get_logger
from solar_agent.utils.correlation import set_correlation_id, clear_correlation_id


class TestStructuredLogging:
    """Test cases for structured logging."""
    
    @pytest.fixture
    def sample_config(self):
        """Create a sample configuration for testing."""
        return SolarAgentConfig(
            site_id="test-site-001",
            agent_id="test-agent-001",
            utility_url="http://localhost:8001",
            weather_mcp_url="http://localhost:8002",
            api_key_solar="test-key",
            log_level="INFO"
        )
    
    @pytest.fixture
    def log_capture(self):
        """Capture log output for testing."""
        # Create a string buffer to capture log output
        log_buffer = StringIO()
        
        # Configure logging to write to our buffer
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            stream=log_buffer
        )
        
        yield log_buffer
        
        # Clean up
        log_buffer.close()
    
    def test_configure_logging_with_config(self, sample_config):
        """Test that configure_logging accepts a config object."""
        # This should not raise any exceptions
        configure_logging(sample_config)
    
    def test_get_logger_returns_bound_logger(self, sample_config):
        """Test that get_logger returns a bound logger with context."""
        configure_logging(sample_config)
        logger = get_logger("test.module")
        
        # Should be a structlog BoundLogger
        assert hasattr(logger, 'bind')
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
    
    def test_logger_includes_context_fields(self, sample_config, log_capture):
        """Test that logger includes site_id and agent_id in context."""
        configure_logging(sample_config)
        logger = get_logger("test.module")
        
        # Log a message
        logger.info("Test message")
        
        # Get the log output
        log_output = log_capture.getvalue().strip()
        
        # Parse the JSON log entry
        log_entry = json.loads(log_output)
        
        # Check that context fields are included
        assert log_entry['site_id'] == "test-site-001"
        assert log_entry['agent_id'] == "test-agent-001"
        assert log_entry['event'] == "Test message"
        assert log_entry['logger'] == "test.module"
        assert log_entry['level'] == "info"
    
    def test_logger_includes_correlation_id(self, sample_config, log_capture):
        """Test that logger includes correlation ID when set."""
        configure_logging(sample_config)
        logger = get_logger("test.module")
        
        # Set correlation ID
        correlation_id = "test-correlation-123"
        set_correlation_id(correlation_id)
        
        # Log a message
        logger.info("Test message with correlation")
        
        # Get the log output
        log_output = log_capture.getvalue().strip()
        
        # Parse the JSON log entry
        log_entry = json.loads(log_output)
        
        # Check that correlation ID is included
        assert log_entry['correlation_id'] == correlation_id
        assert log_entry['event'] == "Test message with correlation"
    
    def test_logger_without_correlation_id(self, sample_config, log_capture):
        """Test that logger works without correlation ID."""
        configure_logging(sample_config)
        logger = get_logger("test.module")
        
        # Clear any existing correlation ID
        clear_correlation_id()
        
        # Log a message
        logger.info("Test message without correlation")
        
        # Get the log output
        log_output = log_capture.getvalue().strip()
        
        # Parse the JSON log entry
        log_entry = json.loads(log_output)
        
        # Check that correlation_id is not present
        assert 'correlation_id' not in log_entry
        assert log_entry['event'] == "Test message without correlation"
    
    def test_logger_includes_timestamp(self, sample_config, log_capture):
        """Test that logger includes timestamp in ISO format."""
        configure_logging(sample_config)
        logger = get_logger("test.module")
        
        # Log a message
        logger.info("Test message with timestamp")
        
        # Get the log output
        log_output = log_capture.getvalue().strip()
        
        # Parse the JSON log entry
        log_entry = json.loads(log_output)
        
        # Check that timestamp is included and is ISO format
        assert 'timestamp' in log_entry
        timestamp = log_entry['timestamp']
        assert isinstance(timestamp, str)
        # Basic ISO format check (should contain 'T' and 'Z' or timezone)
        assert 'T' in timestamp
    
    def test_logger_different_levels(self, sample_config, log_capture):
        """Test that different log levels work correctly."""
        configure_logging(sample_config)
        logger = get_logger("test.module")
        
        # Test different log levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        # Get all log output
        log_output = log_capture.getvalue().strip()
        log_lines = log_output.split('\n')
        
        # Should have 4 log entries (debug might be filtered out depending on level)
        assert len(log_lines) >= 3  # At least info, warning, error
        
        # Parse and check levels
        for line in log_lines:
            if line.strip():
                log_entry = json.loads(line)
                assert log_entry['level'] in ['info', 'warning', 'error']
    
    def test_logger_with_exception(self, sample_config, log_capture):
        """Test that logger handles exceptions correctly."""
        configure_logging(sample_config)
        logger = get_logger("test.module")
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("An error occurred")
        
        # Get the log output
        log_output = log_capture.getvalue().strip()
        
        # Parse the JSON log entry
        log_entry = json.loads(log_output)
        
        # Check that exception info is included
        assert log_entry['level'] == 'error'
        assert log_entry['event'] == "An error occurred"
        assert 'exception' in log_entry
    
    def test_logger_context_isolation(self, sample_config, log_capture):
        """Test that logger context is isolated between different loggers."""
        configure_logging(sample_config)
        
        # Create two different loggers
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        
        # Log messages from both
        logger1.info("Message from module1")
        logger2.info("Message from module2")
        
        # Get the log output
        log_output = log_capture.getvalue().strip()
        log_lines = log_output.split('\n')
        
        # Parse both log entries
        entry1 = json.loads(log_lines[0])
        entry2 = json.loads(log_lines[1])
        
        # Check that they have different logger names
        assert entry1['logger'] == "module1"
        assert entry2['logger'] == "module2"
        
        # But same context fields
        assert entry1['site_id'] == entry2['site_id']
        assert entry1['agent_id'] == entry2['agent_id'] 