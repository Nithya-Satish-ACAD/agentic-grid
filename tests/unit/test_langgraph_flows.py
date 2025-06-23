"""
Unit tests for LangGraph flows.

Tests for anomaly analysis flow with mocked tools.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from solar_agent.ai.langgraph_flows import AnomalyAnalysisFlow, AnomalyState


class TestAnomalyAnalysisFlow:
    """Test cases for AnomalyAnalysisFlow."""
    
    @pytest.fixture
    def mock_weather_tool(self):
        """Create a mock weather tool."""
        tool = Mock()
        tool.get_weather = AsyncMock(return_value={
            'temperature': 25.0,
            'conditions': 'sunny'
        })
        return tool
    
    @pytest.fixture
    def mock_llm_tool(self):
        """Create a mock LLM tool."""
        tool = Mock()
        tool.generate_structured_response = AsyncMock(return_value={
            'causes': ['weather conditions'],
            'severity': 'medium',
            'recommendations': ['check system'],
            'explanation': 'Test explanation'
        })
        return tool
    
    @pytest.fixture
    def mock_prompt_manager(self):
        """Create a mock prompt manager."""
        manager = Mock()
        manager.render_prompt = Mock(return_value="Test prompt")
        return manager
    
    @pytest.fixture
    def flow(self, mock_weather_tool, mock_llm_tool, mock_prompt_manager):
        """Create a test flow instance."""
        return AnomalyAnalysisFlow(
            weather_tool=mock_weather_tool,
            llm_tool=mock_llm_tool,
            prompt_manager=mock_prompt_manager
        )
    
    @pytest.fixture
    def sample_readings(self):
        """Create sample readings data."""
        return [
            {
                'timestamp': '2024-01-15T10:00:00Z',
                'power_kw': 5.0,
                'status': 'normal'
            }
        ]
    
    @pytest.fixture
    def sample_weather(self):
        """Create sample weather data."""
        return {
            'temperature': 25.0,
            'conditions': 'sunny'
        }
    
    @pytest.mark.asyncio
    async def test_analyze_anomaly_returns_dict(self, flow, sample_readings, sample_weather):
        """Test that analyze_anomaly returns a dictionary."""
        result = await flow.analyze_anomaly(sample_readings, sample_weather)
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_analyze_anomaly_has_required_fields(self, flow, sample_readings, sample_weather):
        """Test that analysis result has required fields."""
        result = await flow.analyze_anomaly(sample_readings, sample_weather)
        
        required_fields = ['causes', 'severity', 'recommendations', 'explanation']
        for field in required_fields:
            assert field in result
    
    @pytest.mark.asyncio
    async def test_analyze_anomaly_with_llm_failure(self, flow, sample_readings, sample_weather):
        """Test analysis when LLM tool fails."""
        # Make LLM tool raise an exception
        flow.llm_tool.generate_structured_response.side_effect = Exception("LLM error")
        
        result = await flow.analyze_anomaly(sample_readings, sample_weather)
        
        # Should return fallback analysis
        assert isinstance(result, dict)
        assert 'causes' in result
        assert 'severity' in result
        assert result['severity'] == 'medium'  # Default fallback severity


class TestAnomalyState:
    """Test cases for AnomalyState."""
    
    def test_anomaly_state_creation(self):
        """Test AnomalyState creation."""
        readings = [{'test': 'data'}]
        weather = {'temp': 25}
        analysis = {'result': 'test'}
        
        state = AnomalyState(readings, weather, analysis)
        
        assert state.readings == readings
        assert state.weather == weather
        assert state.analysis_result == analysis 