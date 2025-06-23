"""
Unit tests for anomaly detector.

Tests for anomaly detection functionality.
"""

import pytest
from datetime import datetime
from solar_agent.core.anomaly_detector import AnomalyDetector


class TestAnomalyDetector:
    """Test cases for AnomalyDetector."""
    
    @pytest.fixture
    def detector(self):
        """Create a test anomaly detector instance."""
        return AnomalyDetector(threshold=0.15)
    
    @pytest.fixture
    def sample_reading(self):
        """Create a sample reading."""
        return {
            'timestamp': datetime.utcnow(),
            'power_kw': 5.0,
            'status': 'normal'
        }
    
    @pytest.fixture
    def sample_forecast(self):
        """Create sample forecast points."""
        return [
            {
                'timestamp': datetime.utcnow(),
                'predicted_kw': 5.0,
                'confidence': 0.8
            }
        ]
    
    def test_check_anomaly_returns_tuple(self, detector, sample_reading, sample_forecast):
        """Test that check_anomaly returns a tuple."""
        result = detector.check_anomaly(sample_reading, sample_forecast)
        assert isinstance(result, tuple)
        assert len(result) == 2
    
    def test_no_anomaly_with_matching_values(self, detector, sample_reading, sample_forecast):
        """Test that no anomaly is detected when values match."""
        is_anomaly, details = detector.check_anomaly(sample_reading, sample_forecast)
        assert not is_anomaly
        assert details is None
    
    def test_anomaly_detected_with_large_deviation(self, detector, sample_reading, sample_forecast):
        """Test that anomaly is detected with large deviation."""
        # Modify reading to have large deviation
        sample_reading['power_kw'] = 10.0  # 100% deviation from 5.0
        
        is_anomaly, details = detector.check_anomaly(sample_reading, sample_forecast)
        assert is_anomaly
        assert details is not None
        assert 'deviation' in details
        assert details['deviation'] > 0.15
    
    def test_empty_forecast_returns_no_anomaly(self, detector, sample_reading):
        """Test that empty forecast returns no anomaly."""
        is_anomaly, details = detector.check_anomaly(sample_reading, [])
        assert not is_anomaly
        assert details is None
    
    def test_anomaly_details_structure(self, detector, sample_reading, sample_forecast):
        """Test that anomaly details have correct structure."""
        sample_reading['power_kw'] = 10.0  # Create anomaly
        
        is_anomaly, details = detector.check_anomaly(sample_reading, sample_forecast)
        
        if is_anomaly:
            required_fields = [
                'actual_power_kw', 'expected_power_kw', 'deviation',
                'threshold', 'timestamp', 'forecast_confidence'
            ]
            for field in required_fields:
                assert field in details 