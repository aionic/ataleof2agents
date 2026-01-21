"""
Clothing recommendation logic for the Weather-Based Clothing Advisor.

Generates clothing recommendations based on weather conditions including
temperature, precipitation, wind, and humidity.
"""

import sys
import os
from typing import List

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.models import WeatherData, ClothingRecommendation, ClothingItem, ClothingCategory
from shared.constants import (
    classify_temperature,
    requires_wind_protection,
    is_high_wind,
    PRECIP_TYPE_RAIN,
    PRECIP_TYPE_SNOW,
    HUMIDITY_HIGH,
    SC_002_MIN_RECOMMENDATIONS,
    SC_002_MAX_RECOMMENDATIONS
)


class ClothingAdvisor:
    """Generates clothing recommendations based on weather conditions."""

    def generate_recommendations(self, weather: WeatherData) -> ClothingRecommendation:
        """
        Generate clothing recommendations based on weather data.

        Args:
            weather: WeatherData object with current conditions

        Returns:
            ClothingRecommendation with 3-5 specific items
        """
        # Initialize recommendation object
        recommendation = ClothingRecommendation(
            zip_code=weather.zip_code,
            weather_summary=self._create_weather_summary(weather),
            items=[]
        )

        # Classify temperature
        temp_class = classify_temperature(weather.temperature)

        # Generate base recommendations by temperature
        self._add_temperature_recommendations(recommendation, weather, temp_class)

        # Add precipitation-specific recommendations
        if weather.precipitation_type:
            self._add_precipitation_recommendations(recommendation, weather)

        # Add wind-specific recommendations
        if requires_wind_protection(weather.wind_speed):
            self._add_wind_recommendations(recommendation, weather)

        # Ensure we meet SC-002 requirements (3-5 recommendations)
        self._validate_recommendation_count(recommendation)

        return recommendation

    def _create_weather_summary(self, weather: WeatherData) -> str:
        """Create human-readable weather summary."""
        summary = f"{weather.temperature:.0f}°F and {weather.conditions}"

        if weather.precipitation_type:
            summary += f" with {weather.precipitation_type}"

        if weather.wind_speed > 15:
            summary += f", winds at {weather.wind_speed:.0f} mph"

        return summary

    def _add_temperature_recommendations(
        self,
        recommendation: ClothingRecommendation,
        weather: WeatherData,
        temp_class: str
    ):
        """Add base recommendations based on temperature classification."""
        temp = weather.temperature

        if temp_class == "Winter":  # Below 32°F
            recommendation.add_item(ClothingItem(
                category=ClothingCategory.OUTERWEAR,
                item="Heavy winter coat or parka",
                reason=f"Temperature is {temp:.0f}°F (below freezing) - need insulation"
            ))
            recommendation.add_item(ClothingItem(
                category=ClothingCategory.LAYERS,
                item="Thermal base layers and sweater",
                reason="Multiple layers trap heat and provide flexibility"
            ))
            recommendation.add_item(ClothingItem(
                category=ClothingCategory.ACCESSORIES,
                item="Warm hat, gloves, and scarf",
                reason="Extremities lose heat quickly in freezing weather"
            ))

        elif temp_class == "Cool":  # 32-50°F
            recommendation.add_item(ClothingItem(
                category=ClothingCategory.OUTERWEAR,
                item="Medium jacket or fleece",
                reason=f"Temperature is {temp:.0f}°F - need moderate insulation"
            ))
            recommendation.add_item(ClothingItem(
                category=ClothingCategory.LAYERS,
                item="Long sleeves with light sweater",
                reason="Layering allows adjustment as temperature changes"
            ))

        elif temp_class == "Moderate":  # 50-70°F
            recommendation.add_item(ClothingItem(
                category=ClothingCategory.LAYERS,
                item="Long sleeve shirt or light sweater",
                reason=f"Temperature is {temp:.0f}°F - comfortable with light layers"
            ))
            recommendation.add_item(ClothingItem(
                category=ClothingCategory.OUTERWEAR,
                item="Light jacket or cardigan (optional)",
                reason="Carry for cooler moments or indoor AC"
            ))

        elif temp_class == "Warm":  # 70-85°F
            recommendation.add_item(ClothingItem(
                category=ClothingCategory.LAYERS,
                item="T-shirt or short sleeves",
                reason=f"Temperature is {temp:.0f}°F - stay cool with light clothing"
            ))
            if weather.humidity > HUMIDITY_HIGH:
                recommendation.add_item(ClothingItem(
                    category=ClothingCategory.LAYERS,
                    item="Breathable, moisture-wicking fabric",
                    reason=f"Humidity is {weather.humidity}% - helps manage perspiration"
                ))

        else:  # Hot: Above 85°F
            recommendation.add_item(ClothingItem(
                category=ClothingCategory.LAYERS,
                item="Lightweight, loose-fitting clothes",
                reason=f"Temperature is {temp:.0f}°F - maximize air circulation"
            ))
            recommendation.add_item(ClothingItem(
                category=ClothingCategory.ACCESSORIES,
                item="Sun hat and sunglasses",
                reason="Protect from intense sun exposure"
            ))
            if weather.humidity > HUMIDITY_HIGH:
                recommendation.add_item(ClothingItem(
                    category=ClothingCategory.LAYERS,
                    item="Moisture-wicking athletic wear",
                    reason=f"High humidity ({weather.humidity}%) - stay dry and comfortable"
                ))

    def _add_precipitation_recommendations(
        self,
        recommendation: ClothingRecommendation,
        weather: WeatherData
    ):
        """Add precipitation-specific recommendations."""
        if weather.precipitation_type == PRECIP_TYPE_RAIN:
            recommendation.add_item(ClothingItem(
                category=ClothingCategory.OUTERWEAR,
                item="Waterproof rain jacket",
                reason="Rain expected - stay dry with water-resistant layer"
            ))
            recommendation.add_item(ClothingItem(
                category=ClothingCategory.FOOTWEAR,
                item="Waterproof boots or shoes",
                reason="Keep feet dry in wet conditions"
            ))
            recommendation.add_item(ClothingItem(
                category=ClothingCategory.ACCESSORIES,
                item="Umbrella",
                reason="Extra protection from rain"
            ))

        elif weather.precipitation_type == PRECIP_TYPE_SNOW:
            recommendation.add_item(ClothingItem(
                category=ClothingCategory.OUTERWEAR,
                item="Insulated, waterproof winter coat",
                reason="Snow expected - need warmth and water resistance"
            ))
            recommendation.add_item(ClothingItem(
                category=ClothingCategory.FOOTWEAR,
                item="Insulated winter boots with good traction",
                reason="Snow creates slippery, wet conditions"
            ))
            recommendation.add_item(ClothingItem(
                category=ClothingCategory.ACCESSORIES,
                item="Waterproof gloves and warm hat",
                reason="Keep extremities warm and dry in snow"
            ))

    def _add_wind_recommendations(
        self,
        recommendation: ClothingRecommendation,
        weather: WeatherData
    ):
        """Add wind-specific recommendations."""
        wind_mph = weather.wind_speed

        if is_high_wind(wind_mph):
            # High wind: >25 mph
            recommendation.add_item(ClothingItem(
                category=ClothingCategory.OUTERWEAR,
                item="Wind-resistant outer layer",
                reason=f"Strong winds at {wind_mph:.0f} mph - need wind protection"
            ))
        elif requires_wind_protection(wind_mph):
            # Moderate wind: 15-25 mph
            recommendation.add_item(ClothingItem(
                category=ClothingCategory.OUTERWEAR,
                item="Windbreaker or wind-resistant jacket",
                reason=f"Breezy conditions at {wind_mph:.0f} mph - blocks wind chill"
            ))

    def _validate_recommendation_count(self, recommendation: ClothingRecommendation):
        """
        Ensure recommendation count meets SC-002 (3-5 items).

        Removes excess items or adds padding if needed.
        """
        item_count = len(recommendation.items)

        # Too many items: trim to 5
        if item_count > SC_002_MAX_RECOMMENDATIONS:
            # Prioritize: outerwear > accessories > layers > footwear
            priority_order = [
                ClothingCategory.OUTERWEAR,
                ClothingCategory.ACCESSORIES,
                ClothingCategory.LAYERS,
                ClothingCategory.FOOTWEAR
            ]

            # Sort by priority
            sorted_items = []
            for category in priority_order:
                category_items = [item for item in recommendation.items if item.category == category]
                sorted_items.extend(category_items)

            # Keep top 5
            recommendation.items = sorted_items[:SC_002_MAX_RECOMMENDATIONS]

        # Too few items: add generic recommendations
        elif item_count < SC_002_MIN_RECOMMENDATIONS:
            while len(recommendation.items) < SC_002_MIN_RECOMMENDATIONS:
                # Add sensible filler based on what's missing
                existing_categories = {item.category for item in recommendation.items}

                if ClothingCategory.FOOTWEAR not in existing_categories:
                    recommendation.add_item(ClothingItem(
                        category=ClothingCategory.FOOTWEAR,
                        item="Comfortable walking shoes",
                        reason="Appropriate footwear for daily activities"
                    ))
                elif ClothingCategory.ACCESSORIES not in existing_categories:
                    recommendation.add_item(ClothingItem(
                        category=ClothingCategory.ACCESSORIES,
                        item="Watch the forecast",
                        reason="Weather can change - be prepared to adjust"
                    ))
                else:
                    # Shouldn't reach here, but safety net
                    break
