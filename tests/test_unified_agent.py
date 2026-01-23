#!/usr/bin/env python3
"""
Test Unified Agent Package

Tests the unified agent package that works for both Container Apps
and Foundry Hosted deployments.

Usage:
    pytest tests/test_unified_agent.py -v

    # With specific deployment target
    DEPLOYMENT_TARGET=container-app pytest tests/test_unified_agent.py -v
    DEPLOYMENT_TARGET=foundry pytest tests/test_unified_agent.py -v
"""

import os
import sys
import pytest
from typing import Dict, Any
from unittest.mock import MagicMock, patch, AsyncMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestConstants:
    """Test the constants module."""

    def test_temperature_classification(self):
        """Test temperature classification function."""
        from agent.core.constants import classify_temperature

        assert classify_temperature(20) == "Winter"
        assert classify_temperature(40) == "Cool"
        assert classify_temperature(60) == "Moderate"
        assert classify_temperature(75) == "Warm"
        assert classify_temperature(95) == "Hot"

    def test_wind_protection_thresholds(self):
        """Test wind protection determination."""
        from agent.core.constants import requires_wind_protection, is_high_wind

        assert not requires_wind_protection(10)
        assert requires_wind_protection(20)
        assert not is_high_wind(20)
        assert is_high_wind(30)


class TestModels:
    """Test the models module."""

    def test_weather_data_creation(self):
        """Test WeatherData model."""
        from agent.core.models import WeatherData

        weather = WeatherData(
            zip_code="10001",
            location="New York, NY",
            temperature=45.0,
            feels_like=42.0,
            humidity=65,
            wind_speed=12.0,
            description="Cloudy",
        )

        assert weather.zip_code == "10001"
        assert weather.temperature == 45.0

        # Test serialization
        data = weather.to_dict()
        assert data["location"] == "New York, NY"

        # Test deserialization
        weather2 = WeatherData.from_dict(data)
        assert weather2.temperature == weather.temperature

    def test_clothing_item_creation(self):
        """Test ClothingItem model."""
        from agent.core.models import ClothingItem, ClothingCategory

        item = ClothingItem(
            name="Winter coat",
            category=ClothingCategory.OUTERWEAR,
            reason="Cold weather protection",
            priority=1,
        )

        assert item.name == "Winter coat"
        assert item.category == ClothingCategory.OUTERWEAR

        data = item.to_dict()
        assert data["category"] == "outerwear"

    def test_responses_api_request(self):
        """Test ResponsesApiRequest model for Foundry compatibility."""
        from agent.core.models import ResponsesApiRequest

        request = ResponsesApiRequest.from_dict({
            "messages": [{"role": "user", "content": "What to wear in 10001?"}],
            "conversation_id": "test-123",
            "stream": False,
        })

        assert len(request.messages) == 1
        assert request.conversation_id == "test-123"
        assert not request.stream


class TestClothingLogic:
    """Test the clothing recommendation logic."""

    def test_generate_recommendations_cold(self):
        """Test recommendations for cold weather."""
        from agent.core.clothing_logic import ClothingAdvisor
        from agent.core.models import WeatherData

        advisor = ClothingAdvisor()
        weather = WeatherData(
            zip_code="10001",
            location="New York, NY",
            temperature=25.0,
            feels_like=20.0,
            humidity=50,
            wind_speed=10.0,
            description="Clear",
        )

        recommendation = advisor.generate_recommendations(weather)

        assert recommendation.temperature_category == "Winter"
        assert 3 <= len(recommendation.items) <= 5  # SC-002 requirement
        assert any("coat" in item.name.lower() for item in recommendation.items)

    def test_generate_recommendations_hot(self):
        """Test recommendations for hot weather."""
        from agent.core.clothing_logic import ClothingAdvisor
        from agent.core.models import WeatherData

        advisor = ClothingAdvisor()
        weather = WeatherData(
            zip_code="90210",
            location="Beverly Hills, CA",
            temperature=95.0,
            feels_like=98.0,
            humidity=30,
            wind_speed=5.0,
            description="Sunny",
        )

        recommendation = advisor.generate_recommendations(weather)

        assert recommendation.temperature_category == "Hot"
        assert 3 <= len(recommendation.items) <= 5
        assert any("light" in item.name.lower() or "breathable" in item.name.lower()
                   for item in recommendation.items)

    def test_generate_recommendations_rain(self):
        """Test recommendations for rainy weather."""
        from agent.core.clothing_logic import ClothingAdvisor
        from agent.core.models import WeatherData

        advisor = ClothingAdvisor()
        weather = WeatherData(
            zip_code="98101",
            location="Seattle, WA",
            temperature=55.0,
            feels_like=52.0,
            humidity=85,
            wind_speed=8.0,
            description="Light rain",
            precipitation_type="rain",
        )

        recommendation = advisor.generate_recommendations(weather)

        assert "Precipitation expected" in str(recommendation.special_considerations)
        assert any("waterproof" in item.name.lower() or "rain" in item.name.lower()
                   for item in recommendation.items)


class TestAgentService:
    """Test the agent service."""

    @pytest.fixture
    def mock_weather_api(self):
        """Mock weather API responses."""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "zip_code": "10001",
                "location": "New York, NY",
                "temperature": 45.0,
                "feels_like": 42.0,
                "humidity": 65,
                "wind_speed": 12.0,
                "description": "Cloudy",
                "conditions": ["clouds"],
            }
            mock_get.return_value = mock_response
            yield mock_get

    def test_agent_service_init_requires_weather_url(self):
        """Test that AgentService requires WEATHER_API_URL."""
        from agent.core.agent_service import AgentService

        # Clear env var if set
        old_val = os.environ.pop("WEATHER_API_URL", None)

        try:
            with pytest.raises(ValueError, match="WEATHER_API_URL"):
                AgentService()
        finally:
            if old_val:
                os.environ["WEATHER_API_URL"] = old_val

    def test_agent_service_init_with_url(self, mock_weather_api):
        """Test AgentService initialization with URL."""
        from agent.core.agent_service import AgentService

        # Mock the agent framework
        with patch("agent.core.agent_service.AGENT_FRAMEWORK_AVAILABLE", False):
            service = AgentService(weather_api_url="http://test:8080")
            assert service.weather_api_url == "http://test:8080"
            assert service.agent is None  # Mock mode

    def test_call_weather_function(self, mock_weather_api):
        """Test weather function call."""
        from agent.core.agent_service import AgentService

        with patch("agent.core.agent_service.AGENT_FRAMEWORK_AVAILABLE", False):
            service = AgentService(weather_api_url="http://test:8080")
            result = service._call_weather_function("10001")

            assert result["location"] == "New York, NY"
            assert result["temperature"] == 45.0


class TestResponsesServer:
    """Test the Foundry Responses API server."""

    @pytest.fixture
    def mock_agent_service(self):
        """Create a mock agent service."""
        service = MagicMock()
        service.process_message = AsyncMock(return_value={
            "response": "Wear a warm coat!",
            "session_id": "test-123",
            "metadata": {"response_time": 0.5}
        })
        return service

    @pytest.mark.asyncio
    async def test_handle_responses(self, mock_agent_service):
        """Test the /responses endpoint handler."""
        from agent.hosting.responses_server import ResponsesServer

        server = ResponsesServer(agent_service=mock_agent_service)

        result = await server.handle_responses(
            messages=[{"role": "user", "content": "What to wear in 10001?"}],
            conversation_id="test-123",
        )

        assert "choices" in result
        assert result["choices"][0]["message"]["content"] == "Wear a warm coat!"
        assert result["conversation_id"] == "test-123"

    @pytest.mark.asyncio
    async def test_handle_responses_error(self, mock_agent_service):
        """Test error handling in /responses."""
        from agent.hosting.responses_server import ResponsesServer

        server = ResponsesServer(agent_service=mock_agent_service)

        # Test with no user message
        result = await server.handle_responses(
            messages=[{"role": "system", "content": "You are helpful"}],
        )

        assert "error" in result
        assert result["error"]["code"] == "invalid_request"


class TestTelemetry:
    """Test the telemetry module."""

    def test_telemetry_disabled_without_connection_string(self):
        """Test telemetry is disabled without Application Insights."""
        from agent.telemetry.telemetry import TelemetryService

        # Clear connection string
        old_val = os.environ.pop("APPLICATIONINSIGHTS_CONNECTION_STRING", None)

        try:
            service = TelemetryService()
            assert not service.enabled
        finally:
            if old_val:
                os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"] = old_val

    def test_track_event_disabled(self):
        """Test tracking does nothing when disabled."""
        from agent.telemetry.telemetry import TelemetryService

        old_val = os.environ.pop("APPLICATIONINSIGHTS_CONNECTION_STRING", None)

        try:
            service = TelemetryService()
            # Should not raise
            service.track_event("test_event", {"key": "value"})
        finally:
            if old_val:
                os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"] = old_val


class TestWeatherTool:
    """Test the weather tool module."""

    @pytest.fixture
    def mock_requests(self):
        """Mock requests module."""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "zip_code": "10001",
                "location": "New York, NY",
                "temperature": 45.0,
                "feels_like": 42.0,
                "humidity": 65,
                "wind_speed": 12.0,
                "description": "Cloudy",
            }
            mock_get.return_value = mock_response
            yield mock_get

    def test_weather_tool_get_weather(self, mock_requests):
        """Test WeatherTool.get_weather()."""
        from agent.tools.weather_tool import WeatherTool

        tool = WeatherTool(weather_api_url="http://test:8080")
        result = tool.get_weather("10001")

        assert result["location"] == "New York, NY"
        mock_requests.assert_called_once()

    def test_weather_tool_timeout(self, mock_requests):
        """Test WeatherTool handles timeout."""
        import requests
        from agent.tools.weather_tool import WeatherTool

        mock_requests.side_effect = requests.exceptions.Timeout()

        tool = WeatherTool(weather_api_url="http://test:8080")
        result = tool.get_weather("10001")

        assert "error" in result
        assert result["error"]["error_code"] == "TIMEOUT"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
