"""Mock solar data generator for development and testing."""

import math
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from solar_agent.core.models import SolarData
import asyncio


def generate_mock_solar_data(
    capacity_kw: float = 100.0,
    time_override: Optional[datetime] = None,
    cloud_factor: float = 1.0,
    fault_factor: float = 1.0,
    noise_level: float = 0.05
) -> SolarData:
    """Generate realistic mock solar data.
    
    Args:
        capacity_kw: Solar panel capacity in kW
        time_override: Override timestamp (defaults to current time)
        cloud_factor: Cloud cover factor (0.0 = full clouds, 1.0 = clear sky)
        fault_factor: Fault impact factor (0.0 = total failure, 1.0 = normal)
        noise_level: Random noise level (0.0 = no noise, 0.1 = 10% noise)
        
    Returns:
        SolarData object with realistic values
    """
    now = time_override or datetime.utcnow()
    hour_of_day = now.hour + now.minute / 60.0
    
    # Calculate solar irradiance based on time of day
    if 6 <= hour_of_day <= 18:  # Daylight hours
        # Bell curve for solar irradiance (peak at solar noon)
        solar_noon = 12.0
        irradiance_factor = math.exp(-0.5 * ((hour_of_day - solar_noon) / 3) ** 2)
        base_irradiance = 1000 * irradiance_factor  # W/m²
    else:
        base_irradiance = 0  # Night time
    
    # Apply cloud factor and random variations
    irradiance = base_irradiance * cloud_factor * (1 + random.uniform(-noise_level, noise_level))
    irradiance = max(0, irradiance)
    
    # Calculate power output
    panel_efficiency = 0.2  # 20% base efficiency
    theoretical_output = (irradiance / 1000) * capacity_kw * panel_efficiency
    
    # Apply fault factor
    actual_output = theoretical_output * fault_factor
    
    # Add noise to output
    actual_output *= (1 + random.uniform(-noise_level, noise_level))
    actual_output = max(0, actual_output)
    
    # Calculate voltage and current (simplified DC model)
    if actual_output > 0:
        # Typical DC voltage for solar panels
        voltage = 600 + random.uniform(-20, 20)
        current = (actual_output * 1000) / voltage  # P = V * I
    else:
        voltage = 0
        current = 0
    
    # Panel temperature (affected by irradiance and ambient temperature)
    ambient_temp = 25 + random.uniform(-10, 20)  # Ambient temperature variation
    panel_temp = ambient_temp + (irradiance / 1000) * 25  # Panel heating from sunlight
    
    # Efficiency affected by temperature (decreases with heat)
    temp_coefficient = -0.004  # -0.4% per degree C above 25C
    temp_derating = 1 + temp_coefficient * (panel_temp - 25)
    final_efficiency = panel_efficiency * temp_derating * fault_factor
    final_efficiency = max(0, min(1, final_efficiency))
    
    return SolarData(
        timestamp=now,
        current_output_kw=round(actual_output, 2),
        voltage_v=round(voltage, 1),
        current_a=round(current, 1),
        efficiency=round(final_efficiency, 3),
        temperature_c=round(panel_temp, 1),
        irradiance_w_m2=round(irradiance, 1)
    )


def generate_daily_solar_profile(
    capacity_kw: float = 100.0,
    date: Optional[datetime] = None,
    interval_minutes: int = 15,
    cloud_factor: float = 1.0,
    fault_factor: float = 1.0
) -> List[SolarData]:
    """Generate a full day's solar data profile.
    
    Args:
        capacity_kw: Solar panel capacity in kW
        date: Date for the profile (defaults to today)
        interval_minutes: Data point interval in minutes
        cloud_factor: Cloud cover factor
        fault_factor: Fault impact factor
        
    Returns:
        List of SolarData objects covering 24 hours
    """
    if date is None:
        date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    profile = []
    current_time = date
    end_time = date + timedelta(hours=24)
    
    while current_time < end_time:
        data_point = generate_mock_solar_data(
            capacity_kw=capacity_kw,
            time_override=current_time,
            cloud_factor=cloud_factor,
            fault_factor=fault_factor,
            noise_level=0.02  # Lower noise for smoother profile
        )
        profile.append(data_point)
        current_time += timedelta(minutes=interval_minutes)
    
    return profile


def generate_weather_affected_profile(
    capacity_kw: float = 100.0,
    date: Optional[datetime] = None,
    weather_pattern: str = "partly_cloudy"
) -> List[SolarData]:
    """Generate solar data with specific weather patterns.
    
    Args:
        capacity_kw: Solar panel capacity in kW
        date: Date for the profile
        weather_pattern: Weather pattern type
            - "clear": Clear sunny day
            - "partly_cloudy": Intermittent clouds
            - "overcast": Heavily cloudy
            - "stormy": Storm with very low output
            - "variable": Highly variable conditions
            
    Returns:
        List of SolarData objects with weather effects
    """
    if date is None:
        date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    profile = []
    current_time = date
    end_time = date + timedelta(hours=24)
    
    while current_time < end_time:
        hour = current_time.hour + current_time.minute / 60.0
        
        # Apply weather-specific cloud factors
        if weather_pattern == "clear":
            cloud_factor = 0.95 + random.uniform(0, 0.05)  # 95-100% clear
        elif weather_pattern == "partly_cloudy":
            # Intermittent clouds throughout the day
            cloud_factor = 0.6 + 0.4 * math.sin(hour * 0.3) + random.uniform(-0.2, 0.2)
        elif weather_pattern == "overcast":
            cloud_factor = 0.2 + random.uniform(-0.1, 0.1)  # 10-30% of clear
        elif weather_pattern == "stormy":
            cloud_factor = 0.05 + random.uniform(0, 0.05)  # Very low output
        elif weather_pattern == "variable":
            # Highly variable conditions
            cloud_factor = random.uniform(0.1, 1.0)
        else:
            cloud_factor = 1.0  # Default clear
        
        cloud_factor = max(0, min(1, cloud_factor))
        
        data_point = generate_mock_solar_data(
            capacity_kw=capacity_kw,
            time_override=current_time,
            cloud_factor=cloud_factor,
            fault_factor=1.0,
            noise_level=0.03
        )
        profile.append(data_point)
        current_time += timedelta(minutes=15)
    
    return profile


def simulate_fault_scenario(
    capacity_kw: float = 100.0,
    fault_start_hour: int = 10,
    fault_duration_hours: int = 2,
    fault_severity: float = 0.5,
    date: Optional[datetime] = None
) -> List[SolarData]:
    """Simulate a fault scenario in solar data.
    
    Args:
        capacity_kw: Solar panel capacity in kW
        fault_start_hour: Hour when fault begins (0-23)
        fault_duration_hours: Duration of fault in hours
        fault_severity: Severity of fault (0.0 = total failure, 1.0 = no impact)
        date: Date for the scenario
        
    Returns:
        List of SolarData objects with fault simulation
    """
    if date is None:
        date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    profile = []
    current_time = date
    end_time = date + timedelta(hours=24)
    fault_end_hour = fault_start_hour + fault_duration_hours
    
    while current_time < end_time:
        hour = current_time.hour
        
        # Apply fault during specified period
        if fault_start_hour <= hour < fault_end_hour:
            fault_factor = fault_severity
        else:
            fault_factor = 1.0
        
        data_point = generate_mock_solar_data(
            capacity_kw=capacity_kw,
            time_override=current_time,
            cloud_factor=1.0,  # Clear weather to show fault impact clearly
            fault_factor=fault_factor,
            noise_level=0.02
        )
        profile.append(data_point)
        current_time += timedelta(minutes=15)
    
    return profile


def generate_seasonal_data(
    capacity_kw: float = 100.0,
    season: str = "summer",
    days: int = 7
) -> List[SolarData]:
    """Generate solar data with seasonal characteristics.
    
    Args:
        capacity_kw: Solar panel capacity in kW
        season: Season type ("spring", "summer", "fall", "winter")
        days: Number of days to generate
        
    Returns:
        List of SolarData objects with seasonal patterns
    """
    # Seasonal parameters
    seasonal_params = {
        "spring": {"daylight_hours": 12, "max_irradiance": 900, "cloud_prob": 0.3},
        "summer": {"daylight_hours": 14, "max_irradiance": 1000, "cloud_prob": 0.2},
        "fall": {"daylight_hours": 10, "max_irradiance": 800, "cloud_prob": 0.4},
        "winter": {"daylight_hours": 8, "max_irradiance": 600, "cloud_prob": 0.5},
    }
    
    params = seasonal_params.get(season, seasonal_params["summer"])
    
    profile = []
    start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        
        # Random cloud factor for the day
        if random.random() < params["cloud_prob"]:
            daily_cloud_factor = random.uniform(0.3, 0.7)  # Cloudy day
        else:
            daily_cloud_factor = random.uniform(0.8, 1.0)  # Clear day
        
        # Generate day profile
        day_profile = generate_daily_solar_profile(
            capacity_kw=capacity_kw,
            date=current_date,
            interval_minutes=60,  # Hourly data for multi-day profiles
            cloud_factor=daily_cloud_factor,
            fault_factor=1.0
        )
        
        profile.extend(day_profile)
    
    return profile


class DeviceStateManager:
    """
    Thread-safe, injectable manager for device/agent state.
    Use this as a dependency in FastAPI endpoints.
    """
    def __init__(self, device_ids: List[str]):
        self._lock = asyncio.Lock()
        self._device_ids = device_ids
        self._state: Dict[str, Dict[str, Any]] = {
            agent_id: self._init_device_state(agent_id) for agent_id in device_ids
        }

    def _init_device_state(self, agent_id: str) -> Dict[str, Any]:
        return {
            "agent_id": agent_id,
            "generation_kw": random.uniform(20, 100),
            "consumption_kw": random.uniform(10, 80),
            "forecast_kw": random.uniform(20, 100),
            "curtailment_kw": 0.0,
            "last_updated": datetime.utcnow(),
            "logs": [],
        }

    async def get_all_status(self) -> List[Dict[str, Any]]:
        async with self._lock:
            return [state.copy() for state in self._state.values()]

    async def get_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            state = self._state.get(agent_id)
            return state.copy() if state else None

    async def set_curtailment(self, agent_id: str, curtailment_amount: float) -> bool:
        async with self._lock:
            if agent_id not in self._state:
                return False
            self._state[agent_id]["curtailment_kw"] = float(curtailment_amount)
            self._state[agent_id]["last_updated"] = datetime.utcnow()
            return True

    async def get_devices(self) -> List[str]:
        return self._device_ids.copy()

    async def get_logs(self, agent_id: str = None) -> Any:
        async with self._lock:
            if agent_id:
                state = self._state.get(agent_id)
                return state["logs"] if state else None
            return {aid: state["logs"] for aid, state in self._state.items()}

    async def append_log(self, agent_id: str, log_entry: Dict[str, Any]):
        async with self._lock:
            if agent_id in self._state:
                self._state[agent_id]["logs"].append(log_entry)
                if len(self._state[agent_id]["logs"]) > 100:
                    self._state[agent_id]["logs"] = self._state[agent_id]["logs"][-100:]

    async def periodic_logging(self):
        while True:
            now = datetime.utcnow()
            for agent_id in self._device_ids:
                state = self._state[agent_id]
                log_entry = {
                    "timestamp": now.isoformat(),
                    "generation_kw": state["generation_kw"],
                    "consumption_kw": state["consumption_kw"],
                    "forecast_kw": state["forecast_kw"],
                }
                await self.append_log(agent_id, log_entry)
            await asyncio.sleep(60) 