"""
Unit tests for correlation ID utilities.

Tests for correlation ID generation, storage, and context management.
"""

import pytest
import asyncio
import uuid
from solar_agent.utils.correlation import (
    generate_correlation_id,
    get_current_correlation_id,
    set_correlation_id,
    clear_correlation_id,
    CorrelationContext,
    extract_correlation_id_from_headers,
    add_correlation_id_to_headers
)


class TestCorrelationID:
    """Test cases for correlation ID utilities."""
    
    def test_generate_correlation_id(self):
        """Test that generate_correlation_id returns a valid UUID string."""
        correlation_id = generate_correlation_id()
        
        # Should be a string
        assert isinstance(correlation_id, str)
        
        # Should be a valid UUID
        try:
            uuid.UUID(correlation_id)
        except ValueError:
            pytest.fail(f"Generated correlation_id '{correlation_id}' is not a valid UUID")
    
    def test_set_and_get_correlation_id(self):
        """Test setting and getting correlation ID."""
        test_id = "test-correlation-id-123"
        
        # Initially should be None
        assert get_current_correlation_id() is None
        
        # Set correlation ID
        set_correlation_id(test_id)
        assert get_current_correlation_id() == test_id
        
        # Clear correlation ID
        clear_correlation_id()
        assert get_current_correlation_id() is None
    
    def test_correlation_id_isolation(self):
        """Test that correlation IDs are isolated between different contexts."""
        # Set correlation ID in main context
        main_id = "main-context-id"
        set_correlation_id(main_id)
        assert get_current_correlation_id() == main_id
        
        # Create a new context with different ID
        async def test_context():
            context_id = "context-id"
            set_correlation_id(context_id)
            assert get_current_correlation_id() == context_id
            return get_current_correlation_id()
        
        # Run the context
        result = asyncio.run(test_context())
        assert result == "context-id"
        
        # Main context should still have original ID
        assert get_current_correlation_id() == main_id
    
    def test_correlation_context_manager(self):
        """Test CorrelationContext async context manager."""
        async def test_context_manager():
            # Set initial correlation ID
            set_correlation_id("initial-id")
            
            # Use context manager
            async with CorrelationContext("new-id") as correlation_id:
                assert correlation_id == "new-id"
                assert get_current_correlation_id() == "new-id"
            
            # Should restore original ID
            assert get_current_correlation_id() == "initial-id"
        
        asyncio.run(test_context_manager())
    
    def test_correlation_context_manager_with_generated_id(self):
        """Test CorrelationContext with auto-generated ID."""
        async def test_auto_generated():
            # Use context manager without specifying ID
            async with CorrelationContext() as correlation_id:
                # Should be a valid UUID
                try:
                    uuid.UUID(correlation_id)
                except ValueError:
                    pytest.fail(f"Auto-generated correlation_id '{correlation_id}' is not a valid UUID")
                
                assert get_current_correlation_id() == correlation_id
        
        asyncio.run(test_auto_generated())
    
    def test_correlation_context_manager_restores_none(self):
        """Test that CorrelationContext restores None when no previous ID existed."""
        async def test_restore_none():
            # Clear any existing correlation ID
            clear_correlation_id()
            assert get_current_correlation_id() is None
            
            # Use context manager
            async with CorrelationContext("test-id"):
                assert get_current_correlation_id() == "test-id"
            
            # Should restore None
            assert get_current_correlation_id() is None
        
        asyncio.run(test_restore_none())
    
    def test_extract_correlation_id_from_headers(self):
        """Test extracting correlation ID from HTTP headers."""
        # Test with X-Correlation-ID
        headers = {"X-Correlation-ID": "header-id-123"}
        result = extract_correlation_id_from_headers(headers)
        assert result == "header-id-123"
        
        # Test with X-Request-ID
        headers = {"X-Request-ID": "request-id-456"}
        result = extract_correlation_id_from_headers(headers)
        assert result == "request-id-456"
        
        # Test with no correlation ID
        headers = {"Content-Type": "application/json"}
        result = extract_correlation_id_from_headers(headers)
        assert result is None
        
        # Test with empty headers
        result = extract_correlation_id_from_headers({})
        assert result is None
    
    def test_add_correlation_id_to_headers(self):
        """Test adding correlation ID to HTTP headers."""
        headers = {"Content-Type": "application/json"}
        
        # Add specific correlation ID
        result = add_correlation_id_to_headers(headers, "test-id-123")
        assert result["X-Correlation-ID"] == "test-id-123"
        assert result["Content-Type"] == "application/json"
        
        # Add current correlation ID
        set_correlation_id("current-id-456")
        headers = {"Content-Type": "application/json"}
        result = add_correlation_id_to_headers(headers)
        assert result["X-Correlation-ID"] == "current-id-456"
        
        # Test with no current correlation ID
        clear_correlation_id()
        headers = {"Content-Type": "application/json"}
        result = add_correlation_id_to_headers(headers)
        assert "X-Correlation-ID" not in result
        assert result["Content-Type"] == "application/json"
    
    def test_correlation_id_uniqueness(self):
        """Test that generated correlation IDs are unique."""
        ids = set()
        for _ in range(100):
            correlation_id = generate_correlation_id()
            assert correlation_id not in ids
            ids.add(correlation_id) 