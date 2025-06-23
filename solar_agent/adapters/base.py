"""
Base adapter interface for solar inverter data collection.

This module defines the abstract interface that all inverter adapters must implement.
See backend-structure.md for detailed specification.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class InverterAdapter(ABC):
    """Abstract base class for solar inverter adapters."""
    
    @abstractmethod
    async def get_reading(self) -> Dict[str, Any]:
        """
        Retrieve current reading from the inverter.
        
        Returns:
            Dict containing timestamp, power_kw, status fields
            Format: {'timestamp': ..., 'power_kw': ..., 'status': ...}
        """
        pass
    
    @abstractmethod
    async def apply_command(self, command: str, params: Dict[str, Any]) -> bool:
        """
        Apply a command to the inverter.
        
        Args:
            command: Command to execute (e.g., 'maintenance_mode', 'reset')
            params: Command parameters
            
        Returns:
            True if command was successful, False otherwise
        """
        pass 