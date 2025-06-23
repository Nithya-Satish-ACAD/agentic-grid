"""
Anomaly detector for solar power readings.

This module compares actual readings against predictions to identify anomalies
and triggers LangGraph flows for analysis when thresholds are exceeded.
See backend-structure.md for detailed specification.
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime


class AnomalyDetector:
    """Detects anomalies in power readings compared to forecasts."""
    
    def __init__(self, threshold: float = 0.15):
        """
        Initialize anomaly detector.
        
        Args:
            threshold: Deviation threshold as fraction (0.15 = 15%)
        """
        self.threshold = threshold
        
    def check_anomaly(self, 
                      actual_reading: Dict[str, Any],
                      forecast_points: list[Dict[str, Any]]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if actual reading represents an anomaly compared to forecast.
        
        Args:
            actual_reading: Current reading with timestamp, power_kw, status
            forecast_points: List of forecast points with timestamp, predicted_kw
            
        Returns:
            Tuple of (is_anomaly, anomaly_details)
        """
        # TODO: Implement sophisticated anomaly detection
        # TODO: Add time-based matching between actual and forecast
        # TODO: Consider weather conditions in anomaly assessment
        
        if not forecast_points:
            return False, None
            
        actual_power = actual_reading.get('power_kw', 0)
        actual_time = actual_reading.get('timestamp')
        
        # Find closest forecast point
        closest_forecast = self._find_closest_forecast(actual_time, forecast_points)
        if not closest_forecast:
            return False, None
            
        predicted_power = closest_forecast.get('predicted_kw', 0)
        
        # Calculate deviation
        if predicted_power == 0:
            deviation = 1.0 if actual_power > 0 else 0.0
        else:
            deviation = abs(actual_power - predicted_power) / predicted_power
            
        is_anomaly = deviation > self.threshold
        
        if is_anomaly:
            anomaly_details = {
                'actual_power_kw': actual_power,
                'expected_power_kw': predicted_power,
                'deviation': deviation,
                'threshold': self.threshold,
                'timestamp': actual_time,
                'forecast_confidence': closest_forecast.get('confidence', 0)
            }
            return True, anomaly_details
            
        return False, None
        
    def _find_closest_forecast(self, 
                              actual_time: Any, 
                              forecast_points: list[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Find the forecast point closest to the actual reading time.
        
        Args:
            actual_time: Timestamp of actual reading
            forecast_points: List of forecast points
            
        Returns:
            Closest forecast point or None
        """
        # TODO: Implement proper time-based matching
        # TODO: Handle different timestamp formats
        
        if not forecast_points:
            return None
            
        # For now, return the first forecast point
        # In production, this should find the temporally closest match
        return forecast_points[0] 