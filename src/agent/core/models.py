"""
Data models for the Weather-Based Clothing Advisor.

Defines structured data types for weather data, clothing items,
and recommendations used across all components.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ClothingCategory(Enum):
    """Categories of clothing items."""

    OUTERWEAR = "outerwear"
    LAYERS = "layers"
    ACCESSORIES = "accessories"
    FOOTWEAR = "footwear"


@dataclass
class WeatherData:
    """
    Weather data retrieved from external weather API.

    Matches the response schema in weather-api-tool.json contract.
    """

    zip_code: str
    location: str
    temperature: float  # Fahrenheit
    feels_like: float  # Fahrenheit
    humidity: int  # Percentage
    wind_speed: float  # mph
    description: str  # e.g., "light rain", "clear sky"
    precipitation_type: Optional[str] = None  # "rain", "snow", or None
    precipitation_probability: Optional[float] = None  # 0.0-1.0
    conditions: List[str] = field(default_factory=list)  # Weather condition codes

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "zip_code": self.zip_code,
            "location": self.location,
            "temperature": self.temperature,
            "feels_like": self.feels_like,
            "humidity": self.humidity,
            "wind_speed": self.wind_speed,
            "description": self.description,
            "precipitation_type": self.precipitation_type,
            "precipitation_probability": self.precipitation_probability,
            "conditions": self.conditions,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WeatherData":
        """Create from dictionary."""
        return cls(
            zip_code=data["zip_code"],
            location=data["location"],
            temperature=data["temperature"],
            feels_like=data["feels_like"],
            humidity=data["humidity"],
            wind_speed=data["wind_speed"],
            description=data["description"],
            precipitation_type=data.get("precipitation_type"),
            precipitation_probability=data.get("precipitation_probability"),
            conditions=data.get("conditions", []),
        )


@dataclass
class ClothingItem:
    """
    A specific clothing item recommendation.

    Includes the item name, category, and explanation for why
    it's recommended given current conditions.
    """

    name: str
    category: ClothingCategory
    reason: str  # Why this item is recommended
    priority: int = 1  # 1 = essential, 2 = recommended, 3 = optional

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "category": self.category.value,
            "reason": self.reason,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClothingItem":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            category=ClothingCategory(data["category"]),
            reason=data["reason"],
            priority=data.get("priority", 1),
        )


@dataclass
class ClothingRecommendation:
    """
    Complete clothing recommendation based on weather conditions.

    Contains 3-5 clothing items as per success criteria SC-002,
    along with weather context and summary advice.
    """

    weather: WeatherData
    items: List[ClothingItem]
    summary: str  # Brief summary of overall advice
    temperature_category: str  # "Winter", "Cool", "Moderate", "Warm", "Hot"
    special_considerations: List[str] = field(
        default_factory=list
    )  # Wind, rain, etc.

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "weather": self.weather.to_dict(),
            "items": [item.to_dict() for item in self.items],
            "summary": self.summary,
            "temperature_category": self.temperature_category,
            "special_considerations": self.special_considerations,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClothingRecommendation":
        """Create from dictionary."""
        return cls(
            weather=WeatherData.from_dict(data["weather"]),
            items=[ClothingItem.from_dict(item) for item in data["items"]],
            summary=data["summary"],
            temperature_category=data["temperature_category"],
            special_considerations=data.get("special_considerations", []),
        )


@dataclass
class ChatMessage:
    """A message in the conversation."""

    role: str  # "user", "assistant", or "system"
    content: str
    timestamp: Optional[str] = None  # ISO format timestamp

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "role": self.role,
            "content": self.content,
        }
        if self.timestamp:
            result["timestamp"] = self.timestamp
        return result


@dataclass
class ConversationContext:
    """
    Context for an ongoing conversation.

    Maintains history and any extracted information.
    """

    messages: List[ChatMessage] = field(default_factory=list)
    zip_code: Optional[str] = None  # Extracted from conversation
    last_weather: Optional[WeatherData] = None  # Cached weather data
    session_id: Optional[str] = None  # For telemetry

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.messages.append(ChatMessage(role=role, content=content))

    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history in API format."""
        return [msg.to_dict() for msg in self.messages]


@dataclass
class AgentResponse:
    """
    Response from the agent.

    Used in the /responses API endpoint for Foundry compatibility.
    """

    content: str
    conversation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result: Dict[str, Any] = {
            "content": self.content,
        }
        if self.conversation_id:
            result["conversation_id"] = self.conversation_id
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class ResponsesApiRequest:
    """
    Request format for Foundry Responses API.

    Matches the expected input format for /responses endpoint.
    """

    messages: List[Dict[str, str]]  # [{"role": "user", "content": "..."}]
    conversation_id: Optional[str] = None
    stream: bool = False
    model: Optional[str] = None  # Optional model override

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResponsesApiRequest":
        """Create from dictionary."""
        return cls(
            messages=data.get("messages", []),
            conversation_id=data.get("conversation_id"),
            stream=data.get("stream", False),
            model=data.get("model"),
        )
