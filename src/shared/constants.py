"""
Shared constants for the Weather-Based Clothing Advisor POC.

Defines temperature ranges, clothing categories, and API configuration
used across all components.
"""

from typing import Dict, Tuple

# Temperature Classification Ranges (in Fahrenheit)
# Based on agent-prompts.md temperature guidelines
TEMP_RANGE_FREEZING = (-float('inf'), 32.0)  # Below 32°F: Winter weather
TEMP_RANGE_COOL = (32.0, 50.0)  # 32-50°F: Cool weather
TEMP_RANGE_MODERATE = (50.0, 70.0)  # 50-70°F: Moderate weather
TEMP_RANGE_WARM = (70.0, 85.0)  # 70-85°F: Warm weather
TEMP_RANGE_HOT = (85.0, float('inf'))  # Above 85°F: Hot weather

# Temperature range labels
TEMP_LABEL_FREEZING = "Winter"
TEMP_LABEL_COOL = "Cool"
TEMP_LABEL_MODERATE = "Moderate"
TEMP_LABEL_WARM = "Warm"
TEMP_LABEL_HOT = "Hot"

# Wind speed thresholds (mph)
WIND_THRESHOLD_BREEZY = 15.0  # >15 mph: Recommend wind-resistant layer
WIND_THRESHOLD_WINDY = 25.0  # >25 mph: Emphasize wind protection

# Humidity thresholds (%)
HUMIDITY_HIGH = 70  # >70%: Mention breathability for warm weather
HUMIDITY_LOW = 30  # <30%: Mention dry conditions for cold weather

# Precipitation types
PRECIP_TYPE_RAIN = "rain"
PRECIP_TYPE_SNOW = "snow"
PRECIP_TYPE_NONE = None

# Clothing categories (matches ClothingCategory enum in models.py)
CATEGORY_OUTERWEAR = "outerwear"
CATEGORY_LAYERS = "layers"
CATEGORY_ACCESSORIES = "accessories"
CATEGORY_FOOTWEAR = "footwear"

# Success Criteria Constants
SC_001_RESPONSE_TIME_SECONDS = 5  # Max response time per SC-001
SC_002_MIN_RECOMMENDATIONS = 3  # Minimum recommendations per SC-002
SC_002_MAX_RECOMMENDATIONS = 5  # Maximum recommendations per SC-002

# API Configuration
OPENWEATHERMAP_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
OPENWEATHERMAP_UNITS = "imperial"  # Use Fahrenheit
OPENWEATHERMAP_COUNTRY = "US"  # US zip codes only
OPENWEATHERMAP_TIMEOUT_SECONDS = 3  # API timeout per spec performance goal

# Error codes for WeatherApiError
ERROR_CODE_INVALID_ZIP = "INVALID_ZIP"
ERROR_CODE_API_ERROR = "API_ERROR"
ERROR_CODE_NETWORK_ERROR = "NETWORK_ERROR"
ERROR_CODE_TIMEOUT = "TIMEOUT"
ERROR_CODE_RATE_LIMIT = "RATE_LIMIT"
ERROR_CODE_UNKNOWN = "UNKNOWN_ERROR"

# User-friendly error messages
ERROR_MSG_INVALID_ZIP = "Invalid zip code. Please enter a valid 5-digit US zip code."
ERROR_MSG_API_ERROR = "Unable to retrieve weather data. Please try again."
ERROR_MSG_NETWORK_ERROR = "Network error. Please check your internet connection and try again."
ERROR_MSG_TIMEOUT = "Request timed out. The weather service is taking too long to respond."
ERROR_MSG_RATE_LIMIT = "Too many requests. Please wait a moment and try again."
ERROR_MSG_UNKNOWN = "An unexpected error occurred. Please try again."

# Temperature classification helper
TEMP_RANGES: Dict[str, Tuple[float, float]] = {
    TEMP_LABEL_FREEZING: TEMP_RANGE_FREEZING,
    TEMP_LABEL_COOL: TEMP_RANGE_COOL,
    TEMP_LABEL_MODERATE: TEMP_RANGE_MODERATE,
    TEMP_LABEL_WARM: TEMP_RANGE_WARM,
    TEMP_LABEL_HOT: TEMP_RANGE_HOT,
}


def classify_temperature(temp_fahrenheit: float) -> str:
    """
    Classify temperature into one of five ranges.

    Args:
        temp_fahrenheit: Temperature in Fahrenheit

    Returns:
        Temperature classification label (Winter, Cool, Moderate, Warm, Hot)
    """
    if temp_fahrenheit < 32.0:
        return TEMP_LABEL_FREEZING
    elif temp_fahrenheit < 50.0:
        return TEMP_LABEL_COOL
    elif temp_fahrenheit < 70.0:
        return TEMP_LABEL_MODERATE
    elif temp_fahrenheit < 85.0:
        return TEMP_LABEL_WARM
    else:
        return TEMP_LABEL_HOT


def requires_wind_protection(wind_speed_mph: float) -> bool:
    """
    Determine if wind speed requires wind protection recommendation.

    Args:
        wind_speed_mph: Wind speed in miles per hour

    Returns:
        True if wind protection should be recommended
    """
    return wind_speed_mph > WIND_THRESHOLD_BREEZY


def is_high_wind(wind_speed_mph: float) -> bool:
    """
    Determine if wind speed is high enough to emphasize protection.

    Args:
        wind_speed_mph: Wind speed in miles per hour

    Returns:
        True if wind protection should be emphasized
    """
    return wind_speed_mph > WIND_THRESHOLD_WINDY
