"""
Shared data models for the Weather-Based Clothing Advisor POC.

These dataclasses define the core entities used across all components:
- Location: Geographic location (zip code)
- WeatherData: Current weather conditions
- ClothingItem: Individual clothing recommendation
- ClothingRecommendation: Complete set of recommendations
- WeatherApiError: Error response from weather API

All models are JSON-serializable for API communication.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List
from enum import Enum


class ClothingCategory(str, Enum):
    """Categories for organizing clothing recommendations."""
    OUTERWEAR = "outerwear"
    LAYERS = "layers"
    ACCESSORIES = "accessories"
    FOOTWEAR = "footwear"


@dataclass
class Location:
    """
    Represents a geographic location identified by US zip code.

    Used as input parameter for weather lookup operations.
    """
    zip_code: str  # 5-digit US zip code

    def validate(self) -> bool:
        """Basic format validation for zip code."""
        return len(self.zip_code) == 5 and self.zip_code.isdigit()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class WeatherData:
    """
    Represents current weather conditions for a location.

    Sourced from OpenWeatherMap API, used as input to clothing recommendation logic.
    """
    zip_code: str  # Associated zip code
    temperature: float  # Current temperature in Fahrenheit
    conditions: str  # Weather condition description (e.g., "light rain", "clear sky")
    humidity: int  # Relative humidity percentage (0-100)
    wind_speed: float  # Wind speed in miles per hour
    precipitation_type: Optional[str] = None  # Type of precipitation: "rain", "snow", or None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'WeatherData':
        """Create WeatherData instance from dictionary."""
        return cls(**data)


@dataclass
class ClothingItem:
    """
    Represents a single clothing recommendation item.

    Includes category, specific item, and reasoning for the recommendation.
    """
    category: ClothingCategory  # Category (outerwear, layers, accessories, footwear)
    item: str  # Specific clothing item (e.g., "heavy winter coat", "umbrella")
    reason: str  # Explanation for why this item is recommended

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "category": self.category.value,
            "item": self.item,
            "reason": self.reason
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ClothingItem':
        """Create ClothingItem instance from dictionary."""
        return cls(
            category=ClothingCategory(data["category"]),
            item=data["item"],
            reason=data["reason"]
        )


@dataclass
class ClothingRecommendation:
    """
    Complete set of clothing recommendations for weather conditions.

    Contains 3-5 ClothingItem recommendations organized by category.
    """
    zip_code: str  # Associated zip code
    weather_summary: str  # Brief weather summary for context
    items: List[ClothingItem] = field(default_factory=list)  # List of recommended items

    def add_item(self, category: ClothingCategory, item: str, reason: str) -> None:
        """Add a clothing item recommendation."""
        self.items.append(ClothingItem(category=category, item=item, reason=reason))

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "zip_code": self.zip_code,
            "weather_summary": self.weather_summary,
            "items": [item.to_dict() for item in self.items]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ClothingRecommendation':
        """Create ClothingRecommendation instance from dictionary."""
        items = [ClothingItem.from_dict(item_data) for item_data in data.get("items", [])]
        return cls(
            zip_code=data["zip_code"],
            weather_summary=data["weather_summary"],
            items=items
        )


@dataclass
class WeatherApiError:
    """
    Error response from weather function tool.

    Used when weather API call fails or returns invalid data.
    """
    error_code: str  # Error code (e.g., "INVALID_ZIP", "API_ERROR", "NETWORK_ERROR")
    message: str  # User-friendly error message
    details: Optional[str] = None  # Technical details for debugging

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'WeatherApiError':
        """Create WeatherApiError instance from dictionary."""
        return cls(**data)


# Type aliases for clarity
ZipCode = str
Temperature = float
WindSpeed = float
Humidity = int
