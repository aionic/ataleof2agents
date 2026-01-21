"""Shared package initialization."""

from .models import (
    Location,
    WeatherData,
    ClothingItem,
    ClothingRecommendation,
    WeatherApiError,
    ClothingCategory,
)

from .constants import (
    classify_temperature,
    requires_wind_protection,
    is_high_wind,
    TEMP_LABEL_FREEZING,
    TEMP_LABEL_COOL,
    TEMP_LABEL_MODERATE,
    TEMP_LABEL_WARM,
    TEMP_LABEL_HOT,
    PRECIP_TYPE_RAIN,
    PRECIP_TYPE_SNOW,
    SC_001_RESPONSE_TIME_SECONDS,
    SC_002_MIN_RECOMMENDATIONS,
    SC_002_MAX_RECOMMENDATIONS,
)

from .clothing_logic import ClothingAdvisor

__all__ = [
    # Models
    "Location",
    "WeatherData",
    "ClothingItem",
    "ClothingRecommendation",
    "WeatherApiError",
    "ClothingCategory",
    # Constants and helpers
    "classify_temperature",
    "requires_wind_protection",
    "is_high_wind",
    "TEMP_LABEL_FREEZING",
    "TEMP_LABEL_COOL",
    "TEMP_LABEL_MODERATE",
    "TEMP_LABEL_WARM",
    "TEMP_LABEL_HOT",
    "PRECIP_TYPE_RAIN",
    "PRECIP_TYPE_SNOW",
    "SC_001_RESPONSE_TIME_SECONDS",
    "SC_002_MIN_RECOMMENDATIONS",
    "SC_002_MAX_RECOMMENDATIONS",
    # Clothing logic
    "ClothingAdvisor",
]
