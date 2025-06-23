"""
Integration tests for periodic cycle.

Tests the complete periodic cycle with mocked MCP and Utility.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from solar_agent.core.scheduler import Scheduler
from solar_agent.core.context_manager import ContextManager
from solar_agent.core.forecast_engine import ForecastEngine
from solar_agent.core.anomaly_detector import AnomalyDetector


class TestPeriodicCycle:
    """Test cases for periodic execution cycle."""
    
    @pytest.fixture
    def scheduler(self):
        """Create test scheduler."""
        return Scheduler(interval_seconds=1)  # Short interval for testing
    
    @pytest.fixture
    def context_manager(self):
        """Create test context manager."""
        return ContextManager(max_history_size=10)
    
    @pytest.fixture
    def forecast_engine(self):
        """Create test forecast engine."""
        return ForecastEngine(forecast_horizon_hours=24)
    
    @pytest.fixture
    def anomaly_detector(self):
        """Create test anomaly detector."""
        return AnomalyDetector(threshold=0.15)
    
    @pytest.mark.asyncio
    async def test_scheduler_start_stop(self, scheduler):
        """Test scheduler start and stop functionality."""
        # Start scheduler
        await scheduler.start()
        assert scheduler.is_running
        
        # Stop scheduler
        await scheduler.stop()
        assert not scheduler.is_running
    
    @pytest.mark.asyncio
    async def test_scheduler_callback_execution(self, scheduler):
        """Test that registered callbacks are executed."""
        callback_called = False
        
        async def test_callback():
            nonlocal callback_called
            callback_called = True
        
        # Register callback
        scheduler.register_callback("test", test_callback)
        
        # Start scheduler
        await scheduler.start()
        
        # Wait for callback execution
        await asyncio.sleep(1.5)  # Wait longer than interval
        
        # Stop scheduler
        await scheduler.stop()
        
        # Check if callback was called
        assert callback_called
    
    @pytest.mark.asyncio
    async def test_context_manager_operations(self, context_manager):
        """Test context manager operations."""
        # Add reading
        reading = {
            'timestamp': 1234567890,
            'power_kw': 5.0,
            'status': 'normal'
        }
        context_manager.add_reading(reading)
        
        # Get recent readings
        readings = context_manager.get_recent_readings()
        assert len(readings) == 1
        assert readings[0] == reading
        
        # Get latest reading
        latest = context_manager.get_latest_reading()
        assert latest == reading
    
    @pytest.mark.asyncio
    async def test_forecast_engine_integration(self, forecast_engine, context_manager):
        """Test forecast engine integration."""
        # Add some historical readings
        for i in range(5):
            reading = {
                'timestamp': 1234567890 + i,
                'power_kw': 5.0 + i * 0.1,
                'status': 'normal'
            }
            context_manager.add_reading(reading)
        
        # Get readings and generate forecast
        readings = context_manager.get_recent_readings()
        weather = {'temperature': 25.0, 'conditions': 'sunny'}
        
        forecast = forecast_engine.predict(readings, weather)
        assert isinstance(forecast, list)
        assert len(forecast) == 24
    
    @pytest.mark.asyncio
    async def test_anomaly_detection_integration(self, anomaly_detector, context_manager):
        """Test anomaly detection integration."""
        # Add normal reading
        normal_reading = {
            'timestamp': 1234567890,
            'power_kw': 5.0,
            'status': 'normal'
        }
        context_manager.add_reading(normal_reading)
        
        # Create forecast
        forecast = [
            {
                'timestamp': 1234567890,
                'predicted_kw': 5.0,
                'confidence': 0.8
            }
        ]
        
        # Test normal case
        is_anomaly, details = anomaly_detector.check_anomaly(normal_reading, forecast)
        assert not is_anomaly
        
        # Test anomaly case
        anomaly_reading = {
            'timestamp': 1234567891,
            'power_kw': 10.0,  # Large deviation
            'status': 'normal'
        }
        
        is_anomaly, details = anomaly_detector.check_anomaly(anomaly_reading, forecast)
        assert is_anomaly
        assert details is not None 