"""Abstract base adapter for hardware abstraction."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from solar_agent.core.models import SolarData, FaultStatus
from solar_agent.core.exceptions import AdapterException


class HardwareAdapter(ABC):
    """Abstract base class for hardware adapters.
    
    This interface defines the contract that all hardware adapters must implement
    to provide a consistent interface for the Solar Agent workflow.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the adapter with configuration.
        
        Args:
            config: Configuration dictionary specific to the adapter
        """
        self.config = config
        self.is_connected = False
        self.adapter_type = "base"
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the hardware.
        
        Returns:
            True if connection successful, False otherwise
            
        Raises:
            AdapterException: If connection fails
        """
        raise NotImplementedError("connect() must be implemented in subclass.")
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from the hardware.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        raise NotImplementedError("disconnect() must be implemented in subclass.")
    
    @abstractmethod
    async def read_solar_data(self) -> SolarData:
        """Read current solar panel data.
        
        Returns:
            SolarData object with current readings
            
        Raises:
            AdapterException: If reading fails
        """
        raise NotImplementedError("read_solar_data() must be implemented in subclass.")
    
    @abstractmethod
    async def set_output_limit(self, limit_kw: float) -> bool:
        """Set output power limit for curtailment.
        
        Args:
            limit_kw: Output limit in kilowatts
            
        Returns:
            True if limit set successfully, False otherwise
            
        Raises:
            AdapterException: If setting limit fails
        """
        raise NotImplementedError("set_output_limit() must be implemented in subclass.")
    
    @abstractmethod
    async def get_fault_status(self) -> List[FaultStatus]:
        """Get current fault status.
        
        Returns:
            List of FaultStatus objects representing current faults
            
        Raises:
            AdapterException: If reading fault status fails
        """
        raise NotImplementedError("get_fault_status() must be implemented in subclass.")
    
    @abstractmethod
    async def clear_fault(self, fault_id: str) -> bool:
        """Clear a specific fault.
        
        Args:
            fault_id: Unique identifier of the fault to clear
            
        Returns:
            True if fault cleared successfully, False otherwise
            
        Raises:
            AdapterException: If clearing fault fails
        """
        raise NotImplementedError("clear_fault() must be implemented in subclass.")
    
    @abstractmethod
    async def get_device_info(self) -> Dict[str, Any]:
        """Get device information and capabilities.
        
        Returns:
            Dictionary containing device information
        """
        raise NotImplementedError("get_device_info() must be implemented in subclass.")
    
    @abstractmethod
    async def is_online(self) -> bool:
        """Check if the hardware is online and responsive.
        
        Returns:
            True if hardware is online, False otherwise
        """
        raise NotImplementedError("is_online() must be implemented in subclass.")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform adapter health check.
        
        Returns:
            Dictionary containing health status information
        """
        try:
            is_online = await self.is_online()
            device_info = await self.get_device_info()
            faults = await self.get_fault_status()
            
            return {
                "adapter_type": self.adapter_type,
                "is_connected": self.is_connected,
                "is_online": is_online,
                "device_info": device_info,
                "fault_count": len(faults),
                "critical_faults": len([f for f in faults if f.is_critical]),
                "status": "healthy" if is_online and not any(f.is_critical for f in faults) else "degraded"
            }
        except Exception as e:
            return {
                "adapter_type": self.adapter_type,
                "is_connected": self.is_connected,
                "is_online": False,
                "error": str(e),
                "status": "error"
            }
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get adapter capabilities.
        
        Returns:
            Dictionary describing adapter capabilities
        """
        return {
            "supports_curtailment": True,
            "supports_fault_clearing": True,
            "supports_real_time_data": True,
            "max_output_kw": self.config.get("max_output_kw", 100.0),
            "min_output_kw": self.config.get("min_output_kw", 0.0),
            "read_interval_seconds": self.config.get("read_interval_seconds", 1),
        } 