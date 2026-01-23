"""
Clothing recommendation business logic.

This module generates weather-appropriate clothing recommendations
based on the rules defined in agent-prompts.md contract.
"""

from typing import List

from agent.core.constants import (
    CATEGORY_ACCESSORIES,
    CATEGORY_FOOTWEAR,
    CATEGORY_LAYERS,
    CATEGORY_OUTERWEAR,
    HUMIDITY_HIGH,
    PRECIP_TYPE_RAIN,
    PRECIP_TYPE_SNOW,
    SC_002_MAX_RECOMMENDATIONS,
    SC_002_MIN_RECOMMENDATIONS,
    WIND_THRESHOLD_BREEZY,
    WIND_THRESHOLD_WINDY,
    classify_temperature,
)
from agent.core.models import (
    ClothingCategory,
    ClothingItem,
    ClothingRecommendation,
    WeatherData,
)


class ClothingAdvisor:
    """
    Generates clothing recommendations based on weather conditions.

    Implements the recommendation logic from agent-prompts.md contract:
    - Temperature-based selection (5 ranges)
    - Precipitation-aware recommendations
    - Wind consideration
    - Practical, layered advice
    """

    def generate_recommendations(self, weather: WeatherData) -> ClothingRecommendation:
        """
        Generate clothing recommendations for given weather.

        Args:
            weather: Current weather data

        Returns:
            ClothingRecommendation with 3-5 items per SC-002
        """
        items: List[ClothingItem] = []
        special_considerations: List[str] = []

        # Classify temperature
        temp_category = classify_temperature(weather.temperature)

        # Generate base items for temperature
        items.extend(self._get_temperature_items(temp_category, weather))

        # Add precipitation items
        if weather.precipitation_type:
            precip_items = self._get_precipitation_items(
                weather.precipitation_type, temp_category
            )
            items.extend(precip_items)
            special_considerations.append(
                f"Precipitation expected: {weather.precipitation_type}"
            )

        # Add wind items if needed
        if weather.wind_speed > WIND_THRESHOLD_BREEZY:
            wind_items = self._get_wind_items(weather.wind_speed, temp_category)
            items.extend(wind_items)
            if weather.wind_speed > WIND_THRESHOLD_WINDY:
                special_considerations.append("High winds expected")
            else:
                special_considerations.append("Breezy conditions")

        # Add humidity consideration for warm weather
        if temp_category in ("Warm", "Hot") and weather.humidity > HUMIDITY_HIGH:
            special_considerations.append("High humidity - choose breathable fabrics")

        # Dedupe and prioritize
        items = self._dedupe_and_prioritize(items)

        # Ensure 3-5 items (SC-002)
        items = self._enforce_item_count(items, temp_category, weather)

        # Generate summary
        summary = self._generate_summary(temp_category, weather, special_considerations)

        return ClothingRecommendation(
            weather=weather,
            items=items,
            summary=summary,
            temperature_category=temp_category,
            special_considerations=special_considerations,
        )

    def _get_temperature_items(
        self, temp_category: str, weather: WeatherData
    ) -> List[ClothingItem]:
        """Get base clothing items for temperature range."""
        items = []

        if temp_category == "Winter":
            items.extend(
                [
                    ClothingItem(
                        name="Heavy winter coat",
                        category=ClothingCategory.OUTERWEAR,
                        reason=f"Essential for {weather.temperature:.0f}°F freezing temperatures",
                        priority=1,
                    ),
                    ClothingItem(
                        name="Warm layers (thermal underwear or fleece)",
                        category=ClothingCategory.LAYERS,
                        reason="Provides insulation under your coat",
                        priority=1,
                    ),
                    ClothingItem(
                        name="Winter hat and gloves",
                        category=ClothingCategory.ACCESSORIES,
                        reason="Protects extremities from cold",
                        priority=1,
                    ),
                    ClothingItem(
                        name="Insulated boots",
                        category=ClothingCategory.FOOTWEAR,
                        reason="Keeps feet warm and dry",
                        priority=2,
                    ),
                ]
            )

        elif temp_category == "Cool":
            items.extend(
                [
                    ClothingItem(
                        name="Medium-weight jacket",
                        category=ClothingCategory.OUTERWEAR,
                        reason=f"Appropriate for {weather.temperature:.0f}°F cool weather",
                        priority=1,
                    ),
                    ClothingItem(
                        name="Long-sleeve shirt or sweater",
                        category=ClothingCategory.LAYERS,
                        reason="Provides comfortable warmth",
                        priority=1,
                    ),
                    ClothingItem(
                        name="Light scarf (optional)",
                        category=ClothingCategory.ACCESSORIES,
                        reason="Extra warmth for neck area",
                        priority=3,
                    ),
                ]
            )

        elif temp_category == "Moderate":
            items.extend(
                [
                    ClothingItem(
                        name="Light jacket or cardigan",
                        category=ClothingCategory.OUTERWEAR,
                        reason=f"Perfect for {weather.temperature:.0f}°F mild temperatures",
                        priority=2,
                    ),
                    ClothingItem(
                        name="Long-sleeve shirt or light layers",
                        category=ClothingCategory.LAYERS,
                        reason="Versatile for changing conditions",
                        priority=1,
                    ),
                ]
            )

        elif temp_category == "Warm":
            items.extend(
                [
                    ClothingItem(
                        name="Short-sleeve shirt or light top",
                        category=ClothingCategory.LAYERS,
                        reason=f"Comfortable for {weather.temperature:.0f}°F warm weather",
                        priority=1,
                    ),
                    ClothingItem(
                        name="Light pants or shorts",
                        category=ClothingCategory.LAYERS,
                        reason="Keeps you cool in warm temperatures",
                        priority=1,
                    ),
                    ClothingItem(
                        name="Sunglasses",
                        category=ClothingCategory.ACCESSORIES,
                        reason="Protection from sun",
                        priority=2,
                    ),
                ]
            )

        else:  # Hot
            items.extend(
                [
                    ClothingItem(
                        name="Lightweight, breathable clothing",
                        category=ClothingCategory.LAYERS,
                        reason=f"Essential for {weather.temperature:.0f}°F hot weather",
                        priority=1,
                    ),
                    ClothingItem(
                        name="Shorts or light skirt",
                        category=ClothingCategory.LAYERS,
                        reason="Maximum airflow and comfort",
                        priority=1,
                    ),
                    ClothingItem(
                        name="Wide-brim hat or cap",
                        category=ClothingCategory.ACCESSORIES,
                        reason="Sun protection for face and neck",
                        priority=1,
                    ),
                    ClothingItem(
                        name="Sunglasses",
                        category=ClothingCategory.ACCESSORIES,
                        reason="Eye protection from sun",
                        priority=2,
                    ),
                ]
            )

        return items

    def _get_precipitation_items(
        self, precip_type: str, temp_category: str
    ) -> List[ClothingItem]:
        """Get items for precipitation conditions."""
        items = []

        if precip_type == PRECIP_TYPE_RAIN:
            items.append(
                ClothingItem(
                    name="Waterproof jacket or rain coat",
                    category=ClothingCategory.OUTERWEAR,
                    reason="Stay dry in the rain",
                    priority=1,
                )
            )
            items.append(
                ClothingItem(
                    name="Umbrella",
                    category=ClothingCategory.ACCESSORIES,
                    reason="Additional rain protection",
                    priority=2,
                )
            )
            items.append(
                ClothingItem(
                    name="Waterproof shoes or boots",
                    category=ClothingCategory.FOOTWEAR,
                    reason="Keep feet dry",
                    priority=1,
                )
            )

        elif precip_type == PRECIP_TYPE_SNOW:
            items.append(
                ClothingItem(
                    name="Waterproof winter boots",
                    category=ClothingCategory.FOOTWEAR,
                    reason="Essential for snow and slush",
                    priority=1,
                )
            )
            if temp_category != "Winter":  # Winter items already include gloves
                items.append(
                    ClothingItem(
                        name="Waterproof gloves",
                        category=ClothingCategory.ACCESSORIES,
                        reason="Keeps hands warm and dry in snow",
                        priority=1,
                    )
                )

        return items

    def _get_wind_items(
        self, wind_speed: float, temp_category: str
    ) -> List[ClothingItem]:
        """Get items for windy conditions."""
        items = []

        if wind_speed > WIND_THRESHOLD_WINDY:
            # High wind
            if temp_category in ("Winter", "Cool"):
                items.append(
                    ClothingItem(
                        name="Wind-resistant outer layer",
                        category=ClothingCategory.OUTERWEAR,
                        reason=f"Blocks {wind_speed:.0f} mph winds",
                        priority=1,
                    )
                )
            else:
                items.append(
                    ClothingItem(
                        name="Windbreaker",
                        category=ClothingCategory.OUTERWEAR,
                        reason=f"Protection from {wind_speed:.0f} mph winds",
                        priority=1,
                    )
                )
        else:
            # Moderate wind (WIND_THRESHOLD_BREEZY < wind < WIND_THRESHOLD_WINDY)
            if temp_category in ("Winter", "Cool", "Moderate"):
                items.append(
                    ClothingItem(
                        name="Light windbreaker or jacket",
                        category=ClothingCategory.OUTERWEAR,
                        reason="Light wind protection for breezy conditions",
                        priority=2,
                    )
                )

        return items

    def _dedupe_and_prioritize(
        self, items: List[ClothingItem]
    ) -> List[ClothingItem]:
        """Remove duplicates and sort by priority."""
        seen_names = set()
        unique_items = []

        for item in items:
            # Simple name-based dedup
            if item.name.lower() not in seen_names:
                seen_names.add(item.name.lower())
                unique_items.append(item)

        # Sort by priority (lower number = higher priority)
        unique_items.sort(key=lambda x: x.priority)

        return unique_items

    def _enforce_item_count(
        self, items: List[ClothingItem], temp_category: str, weather: WeatherData
    ) -> List[ClothingItem]:
        """Ensure we have 3-5 items per SC-002."""
        # If too many, keep highest priority
        if len(items) > SC_002_MAX_RECOMMENDATIONS:
            items = items[:SC_002_MAX_RECOMMENDATIONS]

        # If too few, add generic items
        while len(items) < SC_002_MIN_RECOMMENDATIONS:
            # Add sensible defaults based on temperature
            if temp_category in ("Winter", "Cool"):
                if not any(i.category == ClothingCategory.FOOTWEAR for i in items):
                    items.append(
                        ClothingItem(
                            name="Comfortable closed-toe shoes",
                            category=ClothingCategory.FOOTWEAR,
                            reason="Appropriate footwear for cooler weather",
                            priority=3,
                        )
                    )
                else:
                    items.append(
                        ClothingItem(
                            name="Long pants",
                            category=ClothingCategory.LAYERS,
                            reason="Keeps legs warm in cooler weather",
                            priority=3,
                        )
                    )
            else:
                if not any(i.category == ClothingCategory.FOOTWEAR for i in items):
                    items.append(
                        ClothingItem(
                            name="Comfortable shoes",
                            category=ClothingCategory.FOOTWEAR,
                            reason="Appropriate footwear for the weather",
                            priority=3,
                        )
                    )
                else:
                    items.append(
                        ClothingItem(
                            name="Light hat or cap",
                            category=ClothingCategory.ACCESSORIES,
                            reason="Optional sun protection",
                            priority=3,
                        )
                    )

        return items

    def _generate_summary(
        self, temp_category: str, weather: WeatherData, considerations: List[str]
    ) -> str:
        """Generate a brief summary of the recommendation."""
        base = f"For {weather.location} at {weather.temperature:.0f}°F ({temp_category.lower()} weather)"

        if weather.precipitation_type:
            base += f" with {weather.precipitation_type}"

        if weather.wind_speed > WIND_THRESHOLD_BREEZY:
            base += f" and {weather.wind_speed:.0f} mph winds"

        base += ": dress in layers appropriate for the conditions."

        return base
