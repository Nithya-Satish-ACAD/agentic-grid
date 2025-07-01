#!/usr/bin/env python3
"""
Test runner for Solar Agent system.

This script runs comprehensive tests including:
- Unit tests for all modules
- Integration tests for workflow
- API endpoint tests
- Adapter tests
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from solar_agent.core.config import Settings
from solar_agent.core.models import AgentMode, WorkflowState
from solar_agent.adapters import MockAdapter
from solar_agent.workflow.graph import WorkflowManager
from solar_agent.tools.data_generator import DataGenerator


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_adapter():
    """Test hardware adapter functionality."""
    logger.info("Testing Mock Adapter...")
    
    # Initialize data generator and adapter
    data_generator = DataGenerator()
    adapter = MockAdapter(
        agent_id="test-solar-001",
        capacity_kw=100.0,
        data_generator=data_generator
    )
    
    # Test connection
    await adapter.connect()
    health = await adapter.health_check()
    assert health["is_online"], "Adapter should be online"
    
    # Test data reading
    solar_data = await adapter.read_data()
    assert solar_data.current_output_kw >= 0, "Output should be non-negative"
    assert solar_data.voltage_v > 0, "Voltage should be positive"
    
    # Test curtailment
    await adapter.apply_curtailment(50.0)
    curtailed_data = await adapter.read_data()
    assert curtailed_data.current_output_kw <= 50.0, "Output should be curtailed"
    
    # Test fault injection
    await adapter.inject_fault("inverter_fault", "High temperature alarm")
    faults = await adapter.get_faults()
    assert len(faults) > 0, "Should have injected fault"
    
    await adapter.disconnect()
    logger.info("✓ Adapter tests passed")


async def test_workflow():
    """Test LangGraph workflow functionality."""
    logger.info("Testing LangGraph Workflow...")
    
    # Initialize components
    data_generator = DataGenerator()
    adapter = MockAdapter(
        agent_id="test-solar-002",
        capacity_kw=100.0,
        data_generator=data_generator
    )
    await adapter.connect()
    
    # Initialize workflow manager
    workflow_manager = WorkflowManager(
        adapter=adapter,
        enable_persistence=False  # Disable for testing
    )
    
    # Start workflow
    initial_state = {
        "agent_id": "test-solar-002",
        "current_mode": AgentMode.NORMAL,
        "workflow_step": "read_solar_data",
    }
    
    thread_id = await workflow_manager.start_workflow(
        agent_id="test-solar-002",
        initial_state=initial_state
    )
    
    # Run a few workflow iterations
    for i in range(3):
        result = await workflow_manager.run_iteration(thread_id)
        logger.info(f"Workflow iteration {i+1}: {result}")
        await asyncio.sleep(1)
    
    # Test state retrieval
    state = await workflow_manager.get_state(thread_id)
    assert state is not None, "Should have workflow state"
    assert state.agent_id == "test-solar-002", "Correct agent ID"
    
    # Test state updates
    updates = {"current_mode": AgentMode.MAINTENANCE}
    success = await workflow_manager.update_state(thread_id, updates)
    assert success, "State update should succeed"
    
    # Stop workflow
    await workflow_manager.stop_workflow()
    await adapter.disconnect()
    
    logger.info("✓ Workflow tests passed")


async def test_forecasting():
    """Test solar forecasting functionality."""
    logger.info("Testing Solar Forecasting...")
    
    from solar_agent.tools.forecasting import SolarForecaster
    
    # Initialize forecaster
    forecaster = SolarForecaster()
    
    # Test simple forecasting (without LLM)
    forecast = await forecaster.generate_simple_forecast(
        current_output_kw=75.0,
        capacity_kw=100.0,
        time_of_day=12,  # Noon
        cloud_cover=0.3
    )
    
    assert forecast.predicted_output_kw > 0, "Forecast should be positive"
    assert forecast.confidence_level > 0, "Should have confidence level"
    
    logger.info(f"Simple forecast: {forecast.predicted_output_kw:.2f}kW")
    logger.info("✓ Forecasting tests passed")


async def test_mcp_client():
    """Test MCP client functionality."""
    logger.info("Testing MCP Client...")
    
    from solar_agent.tools.mcp_client import MCPClient
    
    # Initialize MCP client (won't actually connect in test)
    client = MCPClient(server_url="ws://test-server:8765")
    
    # Test weather data parsing
    mock_weather = {
        "temperature": 25.0,
        "humidity": 60.0,
        "cloud_cover": 0.3,
        "wind_speed": 5.0,
        "irradiance": 800.0
    }
    
    parsed = client.parse_weather_data(mock_weather)
    assert parsed["temperature"] == 25.0, "Temperature should be parsed"
    assert parsed["irradiance"] == 800.0, "Irradiance should be parsed"
    
    logger.info("✓ MCP Client tests passed")


def test_configuration():
    """Test configuration system."""
    logger.info("Testing Configuration...")
    
    # Test default settings
    settings = Settings()
    assert settings.agent_id is not None, "Should have agent ID"
    assert settings.capacity_kw > 0, "Should have positive capacity"
    assert settings.port > 0, "Should have valid port"
    
    logger.info("✓ Configuration tests passed")


async def test_api_models():
    """Test API model validation."""
    logger.info("Testing API Models...")
    
    from solar_agent.api.models import CurtailmentRequest, StatusResponse
    from solar_agent.core.models import SolarData, CurtailmentCommand
    from datetime import datetime
    
    # Test curtailment request
    curtailment_req = CurtailmentRequest(
        target_output_kw=50.0,
        duration_minutes=60,
        priority=5,
        reason="Grid balancing"
    )
    assert curtailment_req.target_output_kw == 50.0, "Target output should match"
    
    # Test solar data
    solar_data = SolarData(
        current_output_kw=75.0,
        voltage_v=400.0,
        current_a=187.5,
        efficiency=0.85,
        temperature_c=35.0,
        irradiance_w_m2=850.0
    )
    assert solar_data.current_output_kw == 75.0, "Output should match"
    
    logger.info("✓ API Model tests passed")


async def run_all_tests():
    """Run all test suites."""
    logger.info("🚀 Starting Solar Agent Test Suite")
    start_time = time.time()
    
    try:
        # Run synchronous tests
        test_configuration()
        await test_api_models()
        
        # Run async tests
        await test_adapter()
        await test_workflow()
        await test_forecasting()
        await test_mcp_client()
        
        elapsed = time.time() - start_time
        logger.info(f"✅ All tests passed in {elapsed:.2f} seconds")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test runner entry point."""
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 