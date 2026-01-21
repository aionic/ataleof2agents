# Data Model: Weather-Based Clothing Advisor

**Purpose**: Define the core data structures used throughout the application for weather data, location information, and clothing recommendations.

**Phase**: Phase 1 (Design & Contracts)

**Date**: 2026-01-20

## Overview

This document defines the data models used by the Weather-Based Clothing Advisor POC. All models are designed to be simple, JSON-serializable structures suitable for API communication between the Azure Function tool and the AI agent.

**Design Philosophy** (Per POC Constitution):
- Simple data classes/dicts (no complex ORM or database models)
- JSON-compatible types only (str, int, float, list, dict)
- Clear field names with explicit types
- Minimal validation (POC-appropriate)

## Core Entities

### 1. Location

Represents a geographic location identified by US zip code.

**Purpose**: Input parameter for weather lookup operations

**Fields**:

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `zip_code` | string | Yes | 5-digit US zip code | `"10001"` |

**JSON Schema**:

```json
{
  "type": "object",
  "properties": {
    "zip_code": {
      "type": "string",
      "pattern": "^[0-9]{5}$",
      "description": "5-digit US zip code"
    }
  },
  "required": ["zip_code"]
}
```

**Python Representation**:

```python
from dataclasses import dataclass

@dataclass
class Location:
    zip_code: str  # 5-digit US zip code

    def validate(self) -> bool:
        """Basic format validation"""
        return len(self.zip_code) == 5 and self.zip_code.isdigit()
```

**Validation Rules**:
- Must be exactly 5 digits
- Must contain only numeric characters
- No validation of zip code existence (API will handle)

**Example Instances**:

```json
{ "zip_code": "10001" }  // New York, NY
{ "zip_code": "90210" }  // Beverly Hills, CA
{ "zip_code": "60601" }  // Chicago, IL
```

---

### 2. WeatherData

Represents current weather conditions for a location, sourced from OpenWeatherMap API.

**Purpose**: Response from weather function tool, input to clothing recommendation logic

**Fields**:

| Field | Type | Required | Description | Example | Unit |
|-------|------|----------|-------------|---------|------|
| `zip_code` | string | Yes | Associated zip code | `"10001"` | - |
| `temperature` | float | Yes | Current temperature | `72.5` | °F (Fahrenheit) |
| `conditions` | string | Yes | Weather condition description | `"light rain"` | - |
| `humidity` | integer | Yes | Relative humidity | `65` | % (percent) |
| `wind_speed` | float | Yes | Wind speed | `12.5` | mph (miles/hour) |
| `precipitation_type` | string | No | Type of precipitation if any | `"rain"`, `"snow"`, `null` | - |

**JSON Schema**:

```json
{
  "type": "object",
  "properties": {
    "zip_code": {
      "type": "string"
    },
    "temperature": {
      "type": "number",
      "description": "Temperature in Fahrenheit"
    },
    "conditions": {
      "type": "string",
      "description": "Weather condition description"
    },
    "humidity": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100,
      "description": "Relative humidity percentage"
    },
    "wind_speed": {
      "type": "number",
      "minimum": 0,
      "description": "Wind speed in mph"
    },
    "precipitation_type": {
      "type": ["string", "null"],
      "enum": ["rain", "snow", "sleet", null]
    }
  },
  "required": ["zip_code", "temperature", "conditions", "humidity", "wind_speed"]
}
```

**Python Representation**:

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class WeatherData:
    zip_code: str
    temperature: float  # Fahrenheit
    conditions: str
    humidity: int  # Percentage (0-100)
    wind_speed: float  # mph
    precipitation_type: Optional[str] = None  # "rain", "snow", "sleet", or None

    def is_cold(self) -> bool:
        """Check if temperature is below freezing"""
        return self.temperature < 32.0

    def is_hot(self) -> bool:
        """Check if temperature is hot"""
        return self.temperature > 85.0

    def has_precipitation(self) -> bool:
        """Check if there's any precipitation"""
        return self.precipitation_type is not None
```

**Temperature Classification** (per FR-005):

| Range (°F) | Classification | Clothing Category |
|------------|----------------|-------------------|
| < 32 | Freezing/Winter | Winter clothing |
| 32 - 50 | Cold/Cool | Cool weather clothing |
| 50 - 70 | Moderate | Moderate clothing |
| 70 - 85 | Warm | Light clothing |
| > 85 | Hot | Hot weather gear |

**Example Instances**:

```json
// Winter weather (NYC)
{
  "zip_code": "10001",
  "temperature": 28.5,
  "conditions": "snow",
  "humidity": 75,
  "wind_speed": 18.2,
  "precipitation_type": "snow"
}

// Summer weather (LA)
{
  "zip_code": "90210",
  "temperature": 88.0,
  "conditions": "clear sky",
  "humidity": 45,
  "wind_speed": 5.0,
  "precipitation_type": null
}

// Rainy moderate weather (Seattle)
{
  "zip_code": "98101",
  "temperature": 55.0,
  "conditions": "light rain",
  "humidity": 85,
  "wind_speed": 10.5,
  "precipitation_type": "rain"
}
```

---

### 3. ClothingItem

Represents a single clothing item or accessory recommendation.

**Purpose**: Individual recommendation components that form complete outfit suggestions

**Fields**:

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `category` | string | Yes | Clothing category | `"outerwear"`, `"layers"`, `"accessories"`, `"footwear"` |
| `item` | string | Yes | Specific item name | `"heavy winter coat"` |
| `reason` | string | No | Why this item is recommended | `"Temperature below freezing"` |

**JSON Schema**:

```json
{
  "type": "object",
  "properties": {
    "category": {
      "type": "string",
      "enum": ["outerwear", "layers", "accessories", "footwear"]
    },
    "item": {
      "type": "string"
    },
    "reason": {
      "type": "string"
    }
  },
  "required": ["category", "item"]
}
```

**Python Representation**:

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ClothingItem:
    category: str  # "outerwear", "layers", "accessories", "footwear"
    item: str
    reason: Optional[str] = None
```

**Category Definitions**:
- **outerwear**: Jackets, coats, raincoats, windbreakers
- **layers**: Shirts, sweaters, base layers, pants, shorts
- **accessories**: Hats, gloves, scarves, sunglasses, umbrella, sunscreen
- **footwear**: Boots, shoes, sandals

**Example Instances**:

```json
{
  "category": "outerwear",
  "item": "heavy winter coat",
  "reason": "Temperature below freezing (28°F)"
}

{
  "category": "accessories",
  "item": "umbrella",
  "reason": "Light rain expected"
}

{
  "category": "layers",
  "item": "shorts and t-shirt",
  "reason": "Hot weather (88°F)"
}
```

---

### 4. ClothingRecommendation

Represents a complete set of clothing recommendations for given weather conditions.

**Purpose**: Agent output providing actionable clothing advice

**Fields**:

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `zip_code` | string | Yes | Associated zip code | `"10001"` |
| `weather_summary` | string | Yes | Brief weather description | `"Cold and snowy"` |
| `items` | array | Yes | List of recommended clothing items | See below |
| `additional_advice` | string | No | Extra contextual advice | `"Dress in layers"` |

**JSON Schema**:

```json
{
  "type": "object",
  "properties": {
    "zip_code": {
      "type": "string"
    },
    "weather_summary": {
      "type": "string"
    },
    "items": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/ClothingItem"
      },
      "minItems": 3,
      "description": "At least 3-5 recommendations (per SC-002)"
    },
    "additional_advice": {
      "type": "string"
    }
  },
  "required": ["zip_code", "weather_summary", "items"]
}
```

**Python Representation**:

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ClothingRecommendation:
    zip_code: str
    weather_summary: str
    items: List[ClothingItem]  # Minimum 3-5 items per SC-002
    additional_advice: Optional[str] = None

    def validate(self) -> bool:
        """Validate recommendation meets success criteria"""
        return len(self.items) >= 3  # SC-002: At least 3-5 recommendations
```

**Example Instance** (Complete Recommendation):

```json
{
  "zip_code": "10001",
  "weather_summary": "Cold and snowy (28°F) with 18 mph winds",
  "items": [
    {
      "category": "outerwear",
      "item": "heavy insulated winter coat",
      "reason": "Temperature below freezing (28°F)"
    },
    {
      "category": "layers",
      "item": "thermal base layers and warm sweater",
      "reason": "Extra warmth needed for sub-freezing temperatures"
    },
    {
      "category": "accessories",
      "item": "warm hat, insulated gloves, and scarf",
      "reason": "Protect extremities in cold weather"
    },
    {
      "category": "footwear",
      "item": "waterproof insulated boots",
      "reason": "Snow on ground, keep feet warm and dry"
    },
    {
      "category": "accessories",
      "item": "windbreaker or wind-resistant outer layer",
      "reason": "High wind speed (18 mph)"
    }
  ],
  "additional_advice": "Dress in layers and cover all exposed skin. Consider limiting time outdoors."
}
```

---

## API Error Responses

### WeatherFunctionError

Represents an error response from the weather function tool.

**Purpose**: Structured error handling for invalid inputs or API failures

**Fields**:

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `error` | boolean | Yes | Always true for errors | `true` |
| `error_code` | string | Yes | Error classification | `"INVALID_ZIP"`, `"API_FAILURE"` |
| `message` | string | Yes | Human-readable error | `"Invalid zip code format"` |
| `zip_code` | string | No | Problematic zip code | `"00000"` |

**JSON Schema**:

```json
{
  "type": "object",
  "properties": {
    "error": {
      "type": "boolean",
      "const": true
    },
    "error_code": {
      "type": "string",
      "enum": ["INVALID_ZIP", "API_FAILURE", "NOT_FOUND"]
    },
    "message": {
      "type": "string"
    },
    "zip_code": {
      "type": "string"
    }
  },
  "required": ["error", "error_code", "message"]
}
```

**Error Codes**:
- `INVALID_ZIP`: Zip code format is invalid (not 5 digits)
- `NOT_FOUND`: Zip code not found in weather API
- `API_FAILURE`: Weather API is unavailable or returned error

**Example Instances**:

```json
// Invalid format
{
  "error": true,
  "error_code": "INVALID_ZIP",
  "message": "Zip code must be exactly 5 digits",
  "zip_code": "123"
}

// Zip code not found
{
  "error": true,
  "error_code": "NOT_FOUND",
  "message": "Weather data not available for this zip code",
  "zip_code": "00000"
}

// API failure
{
  "error": true,
  "error_code": "API_FAILURE",
  "message": "Weather service temporarily unavailable. Please try again later."
}
```

---

## Data Flow

### 1. User Request → Weather Lookup

```text
User Input (Zip Code String)
    ↓
Location { zip_code: "10001" }
    ↓
Azure Function (Weather Tool)
    ↓
OpenWeatherMap API
    ↓
WeatherData { temperature: 72, conditions: "clear", ... }
```

### 2. Weather Data → Clothing Recommendations

```text
WeatherData (from function tool)
    ↓
AI Agent (with instructions + logic)
    ↓
Temperature/Condition Analysis
    ↓
ClothingRecommendation {
    items: [ClothingItem, ...]
}
```

### 3. Error Handling Flow

```text
Invalid Zip Code Input
    ↓
Function Validation
    ↓
WeatherFunctionError { error_code: "INVALID_ZIP", ... }
    ↓
Agent interprets error and provides user-friendly message
```

---

## Implementation Notes

### POC Simplifications

Per POC Constitution Principle I (POC-First Simplicity):

1. **No Database Models**: All data structures are transient (in-memory only)
2. **Minimal Validation**: Basic format checks, no comprehensive validation
3. **No Persistence**: No storage of historical weather or recommendations
4. **Simple Types**: Using Python dataclasses, not complex ORMs
5. **No Caching**: Each request fetches fresh weather data

### Field Naming Conventions

- Snake case for Python (`zip_code`, `weather_summary`)
- Camel case acceptable for JSON APIs if needed
- Clear, descriptive names (no abbreviations except standard units)

### Unit Handling

All units are fixed for POC simplicity:
- Temperature: Fahrenheit (°F) - standard for US weather
- Wind Speed: Miles per hour (mph)
- Humidity: Percentage (0-100)

No unit conversion needed (US zip codes → US units).

---

## References

- Feature Spec: [spec.md](spec.md) - Functional requirements
- Research: [research.md](research.md) - Technology decisions
- OpenWeatherMap API: <https://openweathermap.org/current> - API response format
- Agent Framework: <https://learn.microsoft.com/en-us/agent-framework/> - Tool schemas
