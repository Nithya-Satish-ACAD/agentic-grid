"""Solar forecasting using LLM analysis."""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from ..core.config import settings
from ..core.models import SolarData, GenerationForecast
from ..llm import create_llm_provider, LLMConfig, BaseLLMProvider

logger = logging.getLogger(__name__)


class SolarForecaster:
    """LLM-powered solar generation forecaster."""
    
    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        """Initialize forecaster.
        
        Args:
            llm_provider: Optional LLM provider. If None, creates from settings.
        """
        if llm_provider:
            self.llm = llm_provider
        else:
            # Create LLM provider from settings
            llm_config_dict = settings.get_llm_config()
            llm_config = LLMConfig(**llm_config_dict)
            self.llm = create_llm_provider(
                provider=llm_config.provider,
                model=llm_config.model,
                api_key=llm_config.api_key,
                api_base=llm_config.api_base,
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens,
                timeout=llm_config.timeout
            )
    
    async def generate_forecast(
        self,
        current_data: SolarData,
        historical_data: List[SolarData],
        weather_data: Optional[Dict[str, Any]] = None,
        forecast_hours: int = 24
    ) -> GenerationForecast:
        """Generate solar generation forecast using LLM.
        
        Args:
            current_data: Current solar panel data
            historical_data: Historical solar data for context
            weather_data: Optional weather forecast data
            forecast_hours: Number of hours to forecast
            
        Returns:
            Generation forecast
        """
        try:
            # Prepare context for LLM
            context = self._prepare_forecast_context(
                current_data, historical_data, weather_data, forecast_hours
            )
            
            # Define the forecast schema
            forecast_schema = {
                "type": "object",
                "properties": {
                    "forecast_kw": {"type": "number", "description": "Forecasted generation in kW"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1, "description": "Confidence level"},
                    "peak_hour": {"type": "integer", "minimum": 0, "maximum": 23, "description": "Expected peak generation hour"},
                    "reasoning": {"type": "string", "description": "Brief explanation of the forecast"},
                    "hourly_forecast": {
                        "type": "array",
                        "items": {
                            "type": "object", 
                            "properties": {
                                "hour": {"type": "integer"},
                                "generation_kw": {"type": "number"}
                            }
                        }
                    }
                }
            }
            
            system_prompt = """You are a solar energy forecasting expert. Analyze the provided solar panel data, historical trends, and weather conditions to generate accurate solar generation forecasts.

Consider these factors:
1. Current panel performance and efficiency
2. Historical generation patterns for similar conditions
3. Weather forecast (cloud cover, temperature, solar irradiance)
4. Seasonal variations and sun angle
5. Time of day and daylight hours
6. Any maintenance or fault conditions

Provide realistic forecasts with confidence levels based on data quality and weather certainty."""

            # Generate structured forecast
            forecast_data = await self.llm.generate_structured(
                prompt=context,
                schema=forecast_schema,
                system_prompt=system_prompt
            )
            
            # Create forecast object
            forecast_time = datetime.now()
            valid_until = forecast_time + timedelta(hours=forecast_hours)
            
            return GenerationForecast(
                forecast_time=forecast_time,
                valid_until=valid_until,
                forecasted_generation_kw=forecast_data["forecast_kw"],
                confidence=forecast_data["confidence"],
                conditions=forecast_data.get("reasoning", "LLM-generated forecast"),
                metadata={
                    "peak_hour": forecast_data.get("peak_hour"),
                    "hourly_forecast": forecast_data.get("hourly_forecast", []),
                    "llm_provider": self.llm.provider_name,
                    "model": self.llm.config.model
                }
            )
            
        except Exception as e:
            logger.error(f"Forecast generation failed: {e}")
            # Fallback to simple forecast
            return self._generate_fallback_forecast(current_data, forecast_hours)
    
    def _prepare_forecast_context(
        self,
        current_data: SolarData,
        historical_data: List[SolarData],
        weather_data: Optional[Dict[str, Any]],
        forecast_hours: int
    ) -> str:
        """Prepare context string for LLM."""
        
        context = f"""Solar Generation Forecast Request

Current Solar Panel Status:
- Current Output: {current_data.current_output_kw:.2f} kW
- Voltage: {current_data.voltage_v:.1f} V
- Current: {current_data.current_a:.1f} A
- Efficiency: {current_data.efficiency:.1%}
- Temperature: {current_data.temperature_c:.1f}°C
- Timestamp: {current_data.timestamp}

Panel Specifications:
- Capacity: {settings.capacity_kw} kW
- Location: {settings.location}

Historical Performance (last {len(historical_data)} readings):"""
        
        # Add historical context
        if historical_data:
            recent_avg = sum(d.current_output_kw for d in historical_data[-10:]) / min(10, len(historical_data))
            daily_avg = sum(d.current_output_kw for d in historical_data) / len(historical_data)
            context += f"""
- Recent average (last 10 readings): {recent_avg:.2f} kW
- Overall average: {daily_avg:.2f} kW
- Peak output: {max(d.current_output_kw for d in historical_data):.2f} kW
- Data points: {len(historical_data)}"""
        
        # Add weather context if available
        if weather_data:
            context += f"\n\nWeather Forecast:\n{json.dumps(weather_data, indent=2)}"
        
        context += f"""

Forecast Requirements:
- Duration: {forecast_hours} hours from now
- Provide hourly breakdown
- Include confidence level (0-1)
- Consider weather patterns and historical trends
- Account for daylight hours and solar irradiance patterns

Please analyze this data and provide a detailed solar generation forecast."""
        
        return context
    
    def _generate_fallback_forecast(
        self,
        current_data: SolarData,
        forecast_hours: int
    ) -> GenerationForecast:
        """Generate simple fallback forecast if LLM fails."""
        
        # Simple heuristic: assume current efficiency with daily solar curve
        current_hour = datetime.now().hour
        
        # Basic daily solar curve (peak at noon)
        if 6 <= current_hour <= 18:  # Daylight hours
            peak_factor = 1.0 - abs(current_hour - 12) / 6  # Peak at noon
            estimated_kw = settings.capacity_kw * peak_factor * current_data.efficiency
        else:
            estimated_kw = 0.0  # No generation at night
        
        forecast_time = datetime.now()
        valid_until = forecast_time + timedelta(hours=forecast_hours)
        
        return GenerationForecast(
            forecast_time=forecast_time,
            valid_until=valid_until,
            forecasted_generation_kw=max(0, estimated_kw),
            confidence=0.6,  # Lower confidence for fallback
            conditions="Fallback forecast based on current efficiency and time of day",
            metadata={"method": "fallback", "peak_hour": 12}
        )
    
    async def health_check(self) -> bool:
        """Check if LLM provider is available for forecasting.
        
        Returns:
            True if provider is healthy, False otherwise
        """
        try:
            return await self.llm.health_check()
        except Exception as e:
            logger.warning(f"LLM health check failed: {e}")
            return False


# Convenience function for quick forecasting
async def generate_forecast(
    current_data: SolarData,
    historical_data: Optional[List[SolarData]] = None,
    weather_data: Optional[Dict[str, Any]] = None,
    forecast_hours: int = 24,
    llm_provider: Optional[BaseLLMProvider] = None
) -> GenerationForecast:
    """Generate solar forecast using configured LLM.
    
    Args:
        current_data: Current solar panel data
        historical_data: Historical solar data
        weather_data: Weather forecast data
        forecast_hours: Hours to forecast
        llm_provider: Optional custom LLM provider
        
    Returns:
        Generation forecast
    """
    forecaster = SolarForecaster(llm_provider)
    return await forecaster.generate_forecast(
        current_data=current_data,
        historical_data=historical_data or [],
        weather_data=weather_data,
        forecast_hours=forecast_hours
    ) 