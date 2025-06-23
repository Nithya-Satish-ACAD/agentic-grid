"""
Prometheus metrics configuration for Solar Agent.

This module defines Prometheus counters, gauges, and histograms
for monitoring Solar Agent performance and operations.
See backend-structure.md for detailed specification.
"""

from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from typing import Dict, Any


class SolarAgentMetrics:
    """Prometheus metrics for Solar Agent."""
    
    def __init__(self):
        """Initialize metrics."""
        # Counters
        self.forecasts_sent = Counter(
            'solar_agent_forecasts_sent_total',
            'Total number of forecasts sent to Utility',
            ['agent_id', 'site_id']
        )
        
        self.alerts_sent = Counter(
            'solar_agent_alerts_sent_total',
            'Total number of alerts sent to Utility',
            ['agent_id', 'site_id', 'severity']
        )
        
        self.mcp_calls = Counter(
            'solar_agent_mcp_calls_total',
            'Total number of MCP server calls',
            ['agent_id', 'endpoint', 'status']
        )
        
        self.llm_calls = Counter(
            'solar_agent_llm_calls_total',
            'Total number of LLM API calls',
            ['agent_id', 'model', 'status']
        )
        
        self.errors = Counter(
            'solar_agent_errors_total',
            'Total number of errors',
            ['agent_id', 'component', 'error_type']
        )
        
        # Gauges
        self.current_power = Gauge(
            'solar_agent_current_power_kw',
            'Current power output in kW',
            ['agent_id', 'site_id']
        )
        
        self.cache_size = Gauge(
            'solar_agent_cache_size',
            'Number of items in cache',
            ['agent_id', 'cache_type']
        )
        
        self.scheduler_running = Gauge(
            'solar_agent_scheduler_running',
            'Scheduler running status (1=running, 0=stopped)',
            ['agent_id']
        )
        
        # Histograms
        self.forecast_generation_duration = Histogram(
            'solar_agent_forecast_generation_duration_seconds',
            'Time spent generating forecasts',
            ['agent_id'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        
        self.mcp_call_duration = Histogram(
            'solar_agent_mcp_call_duration_seconds',
            'Time spent on MCP calls',
            ['agent_id', 'endpoint'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        
        self.llm_call_duration = Histogram(
            'solar_agent_llm_call_duration_seconds',
            'Time spent on LLM calls',
            ['agent_id', 'model'],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0]
        )
        
    def record_forecast_sent(self, agent_id: str, site_id: str) -> None:
        """Record a forecast being sent."""
        self.forecasts_sent.labels(agent_id=agent_id, site_id=site_id).inc()
        
    def record_alert_sent(self, agent_id: str, site_id: str, severity: str) -> None:
        """Record an alert being sent."""
        self.alerts_sent.labels(agent_id=agent_id, site_id=site_id, severity=severity).inc()
        
    def record_mcp_call(self, agent_id: str, endpoint: str, status: str) -> None:
        """Record an MCP call."""
        self.mcp_calls.labels(agent_id=agent_id, endpoint=endpoint, status=status).inc()
        
    def record_llm_call(self, agent_id: str, model: str, status: str) -> None:
        """Record an LLM call."""
        self.llm_calls.labels(agent_id=agent_id, model=model, status=status).inc()
        
    def record_error(self, agent_id: str, component: str, error_type: str) -> None:
        """Record an error."""
        self.errors.labels(agent_id=agent_id, component=component, error_type=error_type).inc()
        
    def set_current_power(self, agent_id: str, site_id: str, power_kw: float) -> None:
        """Set current power reading."""
        self.current_power.labels(agent_id=agent_id, site_id=site_id).set(power_kw)
        
    def set_cache_size(self, agent_id: str, cache_type: str, size: int) -> None:
        """Set cache size."""
        self.cache_size.labels(agent_id=agent_id, cache_type=cache_type).set(size)
        
    def set_scheduler_status(self, agent_id: str, running: bool) -> None:
        """Set scheduler running status."""
        self.scheduler_running.labels(agent_id=agent_id).set(1 if running else 0)
        
    def get_metrics_response(self) -> tuple[bytes, str]:
        """Get metrics response for Prometheus scraping."""
        return generate_latest(), CONTENT_TYPE_LATEST


# Global metrics instance
metrics = SolarAgentMetrics() 
 