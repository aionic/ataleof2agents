"""
Weather tool implementation for the agent.

This module provides the get_weather tool that can be registered
with the agent framework.
"""

import json
import logging
import os
import time
from typing import Any, Callable, Dict, Optional

from agent.core.constants import SC_001_RESPONSE_TIME_SECONDS
from agent.telemetry.telemetry import get_telemetry_service

logger = logging.getLogger(__name__)


class WeatherTool:
    """
    Weather tool for retrieving current weather conditions.

    Calls the weather API service and returns formatted weather data.
    """

    def __init__(self, weather_api_url: Optional[str] = None):
        """
        Initialize the weather tool.

        Args:
            weather_api_url: URL of the weather API service. If not provided,
                           reads from WEATHER_API_URL environment variable.
        """
        url = weather_api_url or os.getenv("WEATHER_API_URL")
        if not url:
            raise ValueError("WEATHER_API_URL environment variable is required")
        self.weather_api_url: str = url
        self.telemetry = get_telemetry_service()

    def get_weather(self, zip_code: str) -> Dict[str, Any]:
        """
        Retrieve current weather data for a US zip code.

        Args:
            zip_code: 5-digit US zip code

        Returns:
            Weather data dictionary or error response
        """
        import requests

        start_time = time.time()

        try:
            logger.info(f"Getting weather for zip code: {zip_code}")

            # Call weather API container
            response = requests.get(
                f"{self.weather_api_url}/api/weather",
                params={"zip_code": zip_code},
                timeout=SC_001_RESPONSE_TIME_SECONDS,
            )

            response.raise_for_status()
            result = response.json()

            duration_ms = (time.time() - start_time) * 1000

            # Track dependency
            self.telemetry.track_dependency(
                name="get_weather",
                dependency_type="HTTP",
                target=self.weather_api_url,
                success=True,
                duration_ms=duration_ms,
                properties={"zip_code": zip_code},
            )

            logger.info(
                f"Weather data retrieved for {result.get('location', 'unknown location')}"
            )
            return result

        except requests.exceptions.Timeout:
            duration_ms = (time.time() - start_time) * 1000

            self.telemetry.track_dependency(
                name="get_weather",
                dependency_type="HTTP",
                target=self.weather_api_url,
                success=False,
                duration_ms=duration_ms,
                properties={"zip_code": zip_code, "error": "timeout"},
            )

            logger.error(f"Weather API timeout for zip code: {zip_code}")
            return {
                "error": {
                    "error_code": "TIMEOUT",
                    "message": "Weather request timed out",
                    "details": f"Request exceeded {SC_001_RESPONSE_TIME_SECONDS} seconds",
                }
            }
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            self.telemetry.track_dependency(
                name="get_weather",
                dependency_type="HTTP",
                target=self.weather_api_url,
                success=False,
                duration_ms=duration_ms,
                properties={"zip_code": zip_code, "error": str(e)},
            )

            logger.exception(f"Error calling weather API for zip code: {zip_code}")
            return {
                "error": {
                    "error_code": "API_ERROR",
                    "message": "Error calling weather API",
                    "details": str(e),
                }
            }

    def get_tool_function(self) -> Callable[[str], str]:
        """
        Get the tool function for registration with the agent framework.

        The returned function has proper annotations for the agent framework.

        Returns:
            Callable that takes a zip_code and returns JSON string
        """
        try:
            from typing import Annotated

            from pydantic import Field
        except ImportError:
            # Fallback without annotations
            def get_weather(zip_code: str) -> str:
                """Retrieve current weather data for a US zip code."""
                result = self.get_weather(zip_code)
                return json.dumps(result)

            return get_weather

        def get_weather(
            zip_code: Annotated[str, Field(description="5-digit US zip code")]
        ) -> str:
            """Retrieve current weather data for a US zip code."""
            result = self.get_weather(zip_code)
            return json.dumps(result)

        return get_weather


def create_weather_tool(weather_api_url: Optional[str] = None) -> WeatherTool:
    """
    Factory function to create a WeatherTool instance.

    Args:
        weather_api_url: URL of the weather API service

    Returns:
        Configured WeatherTool instance
    """
    return WeatherTool(weather_api_url)
