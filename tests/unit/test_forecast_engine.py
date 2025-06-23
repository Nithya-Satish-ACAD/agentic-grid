"""
Unit tests for forecast engine.

Tests for power forecasting functionality.
"""

import pytest
from datetime import datetime, timedelta
from solar_agent.core.forecast_engine import ForecastEngine


class TestForecastEngine:
    """Test cases for ForecastEngine."""
    
    @pytest.fixture
    def engine(self):
        """Create a test forecast engine instance."""
        return ForecastEngine(forecast_horizon_hours=24)
    
    @pytest.fixture
    def sample_history(self):
        """Create sample historical readings."""
        base_time = datetime.utcnow()
        return [
            {
                'timestamp': base_time - timedelta(hours=i),
                'power_kw': 5.0 + (i % 3) * 0.5,
                'status': 'normal'
            }
            for i in range(10, 0, -1)
        ]
    
    @pytest.fixture
    def sample_weather(self):
        """Create sample weather data."""
        return {
            'temperature': 25.0,
            'conditions': 'sunny',
            'cloud_cover': 0.1
        }
    
    def test_predict_returns_list(self, engine, sample_history, sample_weather):
        """Test that predict returns a list of forecast points."""
        forecast = engine.predict(sample_history, sample_weather)
        assert isinstance(forecast, list)
        assert len(forecast) == 24  # 24 hours
    
    def test_forecast_points_have_required_fields(self, engine, sample_history, sample_weather):
        """Test that forecast points have required fields."""
        forecast = engine.predict(sample_history, sample_weather)
        
        for point in forecast:
            assert 'timestamp' in point
            assert 'predicted_kw' in point
            assert 'confidence' in point
            assert isinstance(point['timestamp'], datetime)
            assert isinstance(point['predicted_kw'], (int, float))
            assert isinstance(point['confidence'], (int, float))
    
    def test_predict_with_empty_history(self, engine, sample_weather):
        """Test prediction with empty history."""
        forecast = engine.predict([], sample_weather)
        assert isinstance(forecast, list)
        assert len(forecast) == 24
    
    def test_predict_with_no_normal_readings(self, engine, sample_weather):
        """Test prediction with no normal status readings."""
        history = [
            {
                'timestamp': datetime.utcnow() - timedelta(hours=1),
                'power_kw': 0.0,
                'status': 'error'
            }
        ]
        forecast = engine.predict(history, sample_weather)
        assert isinstance(forecast, list)
        assert len(forecast) == 24 