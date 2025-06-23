"""
Context manager for maintaining recent readings history.

This module manages a rolling window of recent inverter readings
for use by the forecast engine and anomaly detector.
See backend-structure.md for detailed specification.
"""

from collections import deque
from typing import List, Dict, Any, Optional
import time


class ContextManager:
    """Manages recent readings history with rolling window."""
    
    def __init__(self, max_history_size: int = 100):
        """
        Initialize context manager.
        
        Args:
            max_history_size: Maximum number of readings to retain
        """
        self.max_history_size = max_history_size
        self.readings_history: deque = deque(maxlen=max_history_size)
        
    def add_reading(self, reading: Dict[str, Any]) -> None:
        """
        Add a new reading to the history.
        
        Args:
            reading: Reading data with timestamp, power_kw, status
        """
        # TODO: Validate reading format
        # TODO: Add timestamp validation
        self.readings_history.append(reading)
        
    def get_recent_readings(self, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get recent readings from history.
        
        Args:
            count: Number of readings to return (default: all available)
            
        Returns:
            List of recent readings, newest first
        """
        if count is None:
            return list(self.readings_history)
        return list(self.readings_history)[-count:]
        
    def get_latest_reading(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent reading.
        
        Returns:
            Latest reading or None if no readings available
        """
        if not self.readings_history:
            return None
        return self.readings_history[-1]
        
    def clear_history(self) -> None:
        """Clear all readings from history."""
        self.readings_history.clear()
        
    def get_history_size(self) -> int:
        """
        Get current number of readings in history.
        
        Returns:
            Number of readings currently stored
        """
        return len(self.readings_history) 