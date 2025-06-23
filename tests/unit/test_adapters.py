"""
Unit tests for solar inverter adapters.

Tests for base adapter interface and simulated adapter implementation.
"""

import pytest
import asyncio
from solar_agent.adapters.base import InverterAdapter
from solar_agent.adapters.simulated import SimulatedAdapter


class TestSimulatedAdapter:
    """Test cases for SimulatedAdapter."""
    
    @pytest.fixture
    def adapter(self):
        """Create a test adapter instance."""
        return SimulatedAdapter(
            failure_rate=0.0,
            base_power_kw=5.0,
            power_variation=1.0
        )
    
    @pytest.mark.asyncio
    async def test_get_reading_returns_dict(self, adapter):
        """Test that get_reading returns a dictionary."""
        reading = await adapter.get_reading()
        assert isinstance(reading, dict)
        assert 'timestamp' in reading
        assert 'power_kw' in reading
        assert 'status' in reading
    
    @pytest.mark.asyncio
    async def test_get_reading_power_range(self, adapter):
        """Test that power readings are within expected range."""
        reading = await adapter.get_reading()
        power = reading['power_kw']
        assert 0 <= power <= 10  # Base 5.0 ± variation 1.0 + some buffer
    
    @pytest.mark.asyncio
    async def test_apply_command_returns_bool(self, adapter):
        """Test that apply_command returns a boolean."""
        result = await adapter.apply_command("test", {})
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_failure_simulation(self):
        """Test failure simulation functionality."""
        # TODO: Implement failure simulation tests
        pass


class TestInverterAdapterInterface:
    """Test cases for InverterAdapter interface."""
    
    def test_adapter_is_abstract(self):
        """Test that InverterAdapter is abstract."""
        with pytest.raises(TypeError):
            InverterAdapter() 