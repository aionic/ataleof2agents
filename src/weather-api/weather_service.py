"""
Weather service that calls OpenWeatherMap API.
"""

import os
import requests
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class WeatherService:
    """Service for fetching weather data from OpenWeatherMap API."""

    def __init__(self):
        """Initialize weather service with API key."""
        self.api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        if not self.api_key:
            raise ValueError("OPENWEATHERMAP_API_KEY environment variable is required")
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        logger.info("Weather service initialized")

    def get_weather(self, zip_code: str) -> Dict[str, Any]:
        """
        Get weather data for a US zip code.

        Args:
            zip_code: 5-digit US zip code

        Returns:
            Dictionary with weather data

        Raises:
            ValueError: If zip code is invalid
            Exception: If API call fails
        """
        if not zip_code or len(zip_code) != 5 or not zip_code.isdigit():
            raise ValueError("Invalid zip code - must be 5 digits")

        try:
            params = {
                "zip": f"{zip_code},US",
                "appid": self.api_key,
                "units": "imperial"
            }

            response = requests.get(
                self.base_url,
                params=params,
                timeout=3
            )

            response.raise_for_status()
            data = response.json()

            # Format response
            result = {
                "location": data["name"],
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "condition": data["weather"][0]["main"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
                "precipitation": data.get("rain", {}).get("1h", 0) + data.get("snow", {}).get("1h", 0)
            }

            logger.info(f"Weather data retrieved for {result['location']}")
            return result

        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching weather for {zip_code}")
            raise Exception("Weather API request timed out")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching weather: {e}")
            if e.response.status_code == 404:
                raise ValueError(f"Zip code {zip_code} not found")
            raise Exception(f"Weather API error: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching weather: {e}")
            raise Exception(f"Failed to fetch weather data: {e}")
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing weather response: {e}")
            raise Exception("Invalid weather data received")
