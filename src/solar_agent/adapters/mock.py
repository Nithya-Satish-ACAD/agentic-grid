"""Mock adapter for development and testing."""

import asyncio
import random
import math
from datetime import datetime
from typing import List, Dict, Any
from solar_agent.core.models import SolarData, FaultStatus
from solar_agent.core.exceptions import AdapterException
from solar_agent.adapters.base import HardwareAdapter


class MockAdapter(HardwareAdapter):
    """Mock hardware adapter for development and testing.
    
    Simulates solar panel behavior with realistic data patterns including:
    - Daily solar irradiance curves
    - Cloud cover effects
    - Temperature variations
    - Random fault injection
    - Curtailment response simulation
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize mock adapter.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.adapter_type = "mock"
        
        # Simulation parameters
        self.base_capacity_kw = config.get("capacity_kw", 100.0)
        self.current_limit_kw = self.base_capacity_kw
        self.fault_probability = config.get("fault_probability", 0.001)  # 0.1% chance per read
        self.cloud_factor = 1.0  # 0.0 to 1.0 (cloudy to clear)
        
        # Current state
        self.active_faults: List[FaultStatus] = []
        self.last_read_time = datetime.utcnow()
        self.connection_stable = True
        
        # Device info
        self.device_info = {
            "manufacturer": "Mock Solar Co.",
            "model": "MockPanel-X1000",
            "serial_number": f"MOCK-{random.randint(100000, 999999)}",
            "firmware_version": "1.2.3",
            "installation_date": "2023-01-01",
            "rated_power_kw": self.base_capacity_kw,
        }
    
    async def connect(self) -> bool:
        """Simulate connection to hardware."""
        # Simulate connection delay
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Simulate occasional connection failures
        if random.random() < 0.05:  # 5% failure rate
            raise AdapterException(
                "Failed to connect to mock hardware",
                adapter_type=self.adapter_type,
                error_code="MOCK_CONNECTION_FAILED"
            )
        
        self.is_connected = True
        return True
    
    async def disconnect(self) -> bool:
        """Simulate disconnection from hardware."""
        await asyncio.sleep(random.uniform(0.05, 0.2))
        self.is_connected = False
        return True
    
    async def read_solar_data(self) -> SolarData:
        """Generate realistic solar data."""
        if not self.is_connected:
            raise AdapterException(
                "Adapter not connected",
                adapter_type=self.adapter_type,
                error_code="NOT_CONNECTED"
            )
        
        # Inject random faults
        await self._maybe_inject_fault()
        
        # Calculate realistic solar data based on time of day
        now = datetime.utcnow()
        hour_of_day = now.hour + now.minute / 60.0
        
        # Simulate daily irradiance curve (peak at noon)
        if 6 <= hour_of_day <= 18:  # Daylight hours
            # Bell curve for solar irradiance
            solar_noon = 12.0
            irradiance_factor = math.exp(-0.5 * ((hour_of_day - solar_noon) / 3) ** 2)
            base_irradiance = 1000 * irradiance_factor  # W/m²
        else:
            base_irradiance = 0  # Night time
        
        # Apply cloud factor and random variations
        irradiance = base_irradiance * self.cloud_factor * random.uniform(0.9, 1.1)
        irradiance = max(0, irradiance)
        
        # Calculate power output based on irradiance and faults
        efficiency = 0.2  # 20% panel efficiency
        fault_factor = 1.0
        for fault in self.active_faults:
            if fault.is_critical:
                fault_factor *= 0.3  # Critical faults reduce output by 70%
            else:
                fault_factor *= 0.8  # Non-critical faults reduce output by 20%
        
        theoretical_output = (irradiance / 1000) * self.base_capacity_kw * efficiency * fault_factor
        
        # Apply curtailment limit
        current_output = min(theoretical_output, self.current_limit_kw)
        
        # Add some noise
        current_output *= random.uniform(0.95, 1.05)
        current_output = max(0, current_output)
        
        # Calculate voltage and current (simplified)
        if current_output > 0:
            voltage = 600 + random.uniform(-20, 20)  # DC voltage
            current = (current_output * 1000) / voltage  # DC current
        else:
            voltage = 0
            current = 0
        
        # Temperature (affects efficiency)
        base_temp = 25 + random.uniform(-5, 35)  # Ambient temperature variation
        panel_temp = base_temp + (irradiance / 1000) * 20  # Panel heating
        
        return SolarData(
            timestamp=now,
            current_output_kw=round(current_output, 2),
            voltage_v=round(voltage, 1),
            current_a=round(current, 1),
            efficiency=round(efficiency * fault_factor, 3),
            temperature_c=round(panel_temp, 1),
            irradiance_w_m2=round(irradiance, 1)
        )
    
    async def set_output_limit(self, limit_kw: float) -> bool:
        """Simulate setting output limit."""
        if not self.is_connected:
            raise AdapterException(
                "Adapter not connected",
                adapter_type=self.adapter_type,
                error_code="NOT_CONNECTED"
            )
        
        if limit_kw < 0 or limit_kw > self.base_capacity_kw:
            raise AdapterException(
                f"Invalid output limit: {limit_kw}kW (max: {self.base_capacity_kw}kW)",
                adapter_type=self.adapter_type,
                error_code="INVALID_LIMIT"
            )
        
        # Simulate command execution delay
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        # Simulate occasional failures
        if random.random() < 0.02:  # 2% failure rate
            raise AdapterException(
                "Failed to set output limit",
                adapter_type=self.adapter_type,
                error_code="CURTAILMENT_FAILED"
            )
        
        self.current_limit_kw = limit_kw
        return True
    
    async def get_fault_status(self) -> List[FaultStatus]:
        """Get current fault status."""
        if not self.is_connected:
            raise AdapterException(
                "Adapter not connected",
                adapter_type=self.adapter_type,
                error_code="NOT_CONNECTED"
            )
        
        return self.active_faults.copy()
    
    async def clear_fault(self, fault_id: str) -> bool:
        """Clear a specific fault."""
        if not self.is_connected:
            raise AdapterException(
                "Adapter not connected",
                adapter_type=self.adapter_type,
                error_code="NOT_CONNECTED"
            )
        
        # Find and remove the fault
        for i, fault in enumerate(self.active_faults):
            if fault.fault_id == fault_id:
                self.active_faults.pop(i)
                return True
        
        return False  # Fault not found
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get device information."""
        return self.device_info.copy()
    
    async def is_online(self) -> bool:
        """Check if device is online."""
        # Simulate occasional connectivity issues
        if random.random() < 0.01:  # 1% chance of being offline
            self.connection_stable = False
        elif random.random() < 0.1:  # 10% chance of recovering
            self.connection_stable = True
        
        return self.is_connected and self.connection_stable
    
    async def _maybe_inject_fault(self) -> None:
        """Randomly inject faults for testing."""
        if random.random() < self.fault_probability:
            fault_types = [
                ("INVERTER_OVERTEMP", "High", "Inverter temperature exceeded threshold", False),
                ("STRING_FAULT", "Medium", "DC string fault detected", False),
                ("GRID_DISCONNECT", "Critical", "Grid connection lost", True),
                ("ARC_FAULT", "Critical", "Arc fault detected in DC circuit", True),
                ("GROUND_FAULT", "High", "Ground fault isolation failure", False),
                ("COMMUNICATION_ERROR", "Low", "Communication timeout with optimizer", False),
            ]
            
            fault_type, severity, description, is_critical = random.choice(fault_types)
            
            fault = FaultStatus(
                fault_type=fault_type,
                severity=severity,
                description=description,
                is_critical=is_critical,
                timestamp=datetime.utcnow()
            )
            
            self.active_faults.append(fault)
    
    def set_cloud_factor(self, factor: float) -> None:
        """Set cloud cover factor for testing.
        
        Args:
            factor: Cloud factor from 0.0 (full clouds) to 1.0 (clear sky)
        """
        self.cloud_factor = max(0.0, min(1.0, factor))
    
    def inject_fault(self, fault_type: str, severity: str, description: str, is_critical: bool = False) -> str:
        """Inject a specific fault for testing.
        
        Args:
            fault_type: Type of fault
            severity: Severity level
            description: Fault description
            is_critical: Whether fault is critical
            
        Returns:
            Fault ID
        """
        fault = FaultStatus(
            fault_type=fault_type,
            severity=severity,
            description=description,
            is_critical=is_critical,
            timestamp=datetime.utcnow()
        )
        
        self.active_faults.append(fault)
        return fault.fault_id 