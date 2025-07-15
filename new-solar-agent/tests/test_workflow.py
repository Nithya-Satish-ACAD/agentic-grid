import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from solar_agent.workflow.state import WorkflowState
from solar_agent.workflow.nodes import read_solar_data
import pytest
import asyncio

class DummyAdapter:
    async def read_solar_data(self):
        class Data:
            generation_kw = 42.0
            irradiance = 0.8
            temperature = 30.0
        return Data()

@pytest.mark.asyncio
async def test_read_solar_data():
    state = WorkflowState(agent_id="test-agent")
    new_state = await read_solar_data(state, DummyAdapter())
    assert "latest_solar_data" in new_state 