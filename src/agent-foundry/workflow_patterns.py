#!/usr/bin/env python3
"""
Story 7: Workflow Orchestration with External APIs
Demonstrates Agent Framework patterns for external API integration.
"""

import os
import sys
import json
import time
import asyncio
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()


# ============================================================================
# Pattern 1: Direct External API Call (No Agent Needed)
# ============================================================================

@dataclass
class WeatherData:
    """Weather data model."""
    location: str
    temperature: float
    feels_like: float
    condition: str
    description: str
    humidity: int
    wind_speed: float


def get_weather_data(zip_code: str) -> WeatherData:
    """
    Direct API call to external weather service.
    No agent needed - pure HTTP request.
    """
    weather_api_url = os.getenv("WEATHER_API_URL")
    if not weather_api_url:
        raise ValueError("WEATHER_API_URL not configured")

    url = f"{weather_api_url}/api/weather"
    response = requests.get(url, params={"zip_code": zip_code}, timeout=10)
    response.raise_for_status()

    data = response.json()
    return WeatherData(
        location=data["location"],
        temperature=data["temperature"],
        feels_like=data["feels_like"],
        condition=data["condition"],
        description=data["description"],
        humidity=data["humidity"],
        wind_speed=data["wind_speed"]
    )


def recommend_clothing_simple(weather: WeatherData) -> List[str]:
    """
    Simple rule-based clothing recommendations.
    Pure Python logic - no AI agent needed.
    """
    recommendations = []

    # Temperature-based recommendations
    if weather.feels_like < 32:
        recommendations.append("Heavy insulated winter coat")
        recommendations.append("Thermal layers")
        recommendations.append("Warm hat and gloves")
    elif weather.feels_like < 50:
        recommendations.append("Warm jacket or sweater")
        recommendations.append("Long pants")
    elif weather.feels_like < 70:
        recommendations.append("Light jacket")
        recommendations.append("Long sleeve shirt")
    else:
        recommendations.append("Light clothing")
        recommendations.append("Shorts and t-shirt")

    # Condition-based recommendations
    condition_lower = weather.condition.lower()
    if "rain" in condition_lower or "drizzle" in condition_lower:
        recommendations.append("Waterproof jacket and umbrella")
    elif "snow" in condition_lower:
        recommendations.append("Waterproof boots")
        recommendations.append("Warm scarf")
    elif "wind" in condition_lower or weather.wind_speed > 15:
        recommendations.append("Windbreaker")

    return recommendations


def workflow_pattern_1_direct_api(zip_code: str) -> Dict[str, Any]:
    """
    Pattern 1: Direct external API workflow (no agent).

    Flow:
    1. Call weather API
    2. Apply business logic
    3. Return results

    Use case: When simple rules suffice, no AI needed.
    """
    print(f"\n{'='*80}")
    print(f"PATTERN 1: Direct External API Call (No Agent)")
    print(f"{'='*80}")

    start_time = time.time()

    # Step 1: Get weather data
    print(f"\nStep 1: Fetching weather for {zip_code}...")
    weather = get_weather_data(zip_code)
    print(f"✓ Weather: {weather.temperature}°F, {weather.condition}")

    # Step 2: Generate recommendations
    print(f"\nStep 2: Generating clothing recommendations...")
    recommendations = recommend_clothing_simple(weather)
    print(f"✓ Generated {len(recommendations)} recommendations")

    duration = time.time() - start_time

    result = {
        "pattern": "direct_api",
        "zip_code": zip_code,
        "weather": {
            "location": weather.location,
            "temperature": weather.temperature,
            "feels_like": weather.feels_like,
            "condition": weather.condition
        },
        "recommendations": recommendations,
        "duration": duration
    }

    print(f"\n✓ Workflow completed in {duration:.2f}s")
    return result


# ============================================================================
# Pattern 2: Concurrent External API Calls
# ============================================================================

def get_weather_batch(zip_codes: List[str]) -> List[WeatherData]:
    """
    Fetch weather data for multiple locations concurrently.
    Demonstrates parallel external API calls.
    """
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_zip = {
            executor.submit(get_weather_data, zip_code): zip_code
            for zip_code in zip_codes
        }

        results = []
        for future in concurrent.futures.as_completed(future_to_zip):
            zip_code = future_to_zip[future]
            try:
                weather = future.result()
                results.append(weather)
            except Exception as e:
                print(f"✗ Error fetching weather for {zip_code}: {e}")

        return results


def workflow_pattern_2_concurrent(zip_codes: List[str]) -> Dict[str, Any]:
    """
    Pattern 2: Concurrent external API calls.

    Flow:
    1. Call multiple weather APIs in parallel
    2. Aggregate results
    3. Generate comparative recommendations

    Use case: When you need data from multiple sources simultaneously.
    """
    print(f"\n{'='*80}")
    print(f"PATTERN 2: Concurrent External API Calls")
    print(f"{'='*80}")

    start_time = time.time()

    # Step 1: Fetch all weather data concurrently
    print(f"\nStep 1: Fetching weather for {len(zip_codes)} locations concurrently...")
    weather_data = get_weather_batch(zip_codes)
    print(f"✓ Fetched {len(weather_data)} weather reports")

    # Step 2: Generate recommendations for each
    print(f"\nStep 2: Generating recommendations for all locations...")
    all_recommendations = []
    for weather in weather_data:
        recs = recommend_clothing_simple(weather)
        all_recommendations.append({
            "location": weather.location,
            "zip_code": next((z for z in zip_codes), None),
            "temperature": weather.temperature,
            "recommendations": recs
        })
    print(f"✓ Generated recommendations for {len(all_recommendations)} locations")

    duration = time.time() - start_time

    result = {
        "pattern": "concurrent_api",
        "locations_count": len(zip_codes),
        "recommendations": all_recommendations,
        "duration": duration
    }

    print(f"\n✓ Workflow completed in {duration:.2f}s (concurrent execution)")
    return result


# ============================================================================
# Pattern 3: Hybrid (External API + Agent Consultation)
# ============================================================================

def workflow_pattern_3_hybrid(zip_code: str, use_agent: bool = True) -> Dict[str, Any]:
    """
    Pattern 3: Hybrid workflow combining external API with optional agent.

    Flow:
    1. Call external weather API
    2. Apply simple rules
    3. If complex reasoning needed, consult agent
    4. Return enhanced recommendations

    Use case: Use external APIs for data, agents for sophisticated reasoning.
    Cost-effective: Only invoke agent when necessary.
    """
    print(f"\n{'='*80}")
    print(f"PATTERN 3: Hybrid (External API + Optional Agent)")
    print(f"{'='*80}")

    start_time = time.time()

    # Step 1: Get weather data from external API
    print(f"\nStep 1: Fetching weather for {zip_code} (external API)...")
    weather = get_weather_data(zip_code)
    print(f"✓ Weather: {weather.temperature}°F, {weather.condition}")

    # Step 2: Apply simple business rules
    print(f"\nStep 2: Applying rule-based recommendations...")
    basic_recommendations = recommend_clothing_simple(weather)
    print(f"✓ Generated {len(basic_recommendations)} basic recommendations")

    # Step 3: Optionally consult agent for enhanced reasoning
    agent_recommendations = None
    if use_agent:
        print(f"\nStep 3: Consulting AI agent for enhanced recommendations...")
        # In production, this would call the Foundry agent
        # For demo, we'll simulate
        agent_recommendations = {
            "enhanced": True,
            "style_tips": "Consider layering for flexibility",
            "activity_suggestions": "Good weather for outdoor activities"
        }
        print(f"✓ Agent provided enhanced insights")
    else:
        print(f"\nStep 3: Skipping agent (simple case)...")

    duration = time.time() - start_time

    result = {
        "pattern": "hybrid",
        "zip_code": zip_code,
        "weather": {
            "location": weather.location,
            "temperature": weather.temperature,
            "condition": weather.condition
        },
        "basic_recommendations": basic_recommendations,
        "agent_enhanced": agent_recommendations,
        "duration": duration
    }

    print(f"\n✓ Workflow completed in {duration:.2f}s")
    return result


# ============================================================================
# Pattern 4: Chained External APIs with Error Handling
# ============================================================================

def get_location_info(zip_code: str) -> Dict[str, Any]:
    """Simulate getting location details from another API."""
    # In production, this would call a real geocoding API
    return {
        "zip_code": zip_code,
        "city": "Example City",
        "state": "EX",
        "timezone": "America/New_York"
    }


def get_historical_weather(zip_code: str) -> Dict[str, Any]:
    """Simulate getting historical weather data."""
    # In production, this would call a historical weather API
    return {
        "average_temp_this_day": 45.0,
        "average_precipitation": 0.5
    }


def workflow_pattern_4_chained(zip_code: str) -> Dict[str, Any]:
    """
    Pattern 4: Chained external API calls with error handling.

    Flow:
    1. Get location info (API 1)
    2. Get current weather (API 2)
    3. Get historical data (API 3)
    4. Combine and analyze
    5. Generate comprehensive recommendations

    Use case: Complex workflows requiring multiple data sources.
    """
    print(f"\n{'='*80}")
    print(f"PATTERN 4: Chained External APIs with Error Handling")
    print(f"{'='*80}")

    start_time = time.time()
    errors = []

    # Step 1: Location info
    print(f"\nStep 1: Fetching location info...")
    try:
        location_info = get_location_info(zip_code)
        print(f"✓ Location: {location_info['city']}, {location_info['state']}")
    except Exception as e:
        errors.append(f"Location API: {str(e)}")
        location_info = None

    # Step 2: Current weather
    print(f"\nStep 2: Fetching current weather...")
    try:
        weather = get_weather_data(zip_code)
        print(f"✓ Current: {weather.temperature}°F, {weather.condition}")
    except Exception as e:
        errors.append(f"Weather API: {str(e)}")
        weather = None

    # Step 3: Historical data
    print(f"\nStep 3: Fetching historical data...")
    try:
        historical = get_historical_weather(zip_code)
        print(f"✓ Historical average: {historical['average_temp_this_day']}°F")
    except Exception as e:
        errors.append(f"Historical API: {str(e)}")
        historical = None

    # Step 4: Generate comprehensive recommendations
    print(f"\nStep 4: Generating comprehensive recommendations...")
    if weather:
        recommendations = recommend_clothing_simple(weather)

        # Add comparative analysis if we have historical data
        if historical:
            temp_diff = weather.temperature - historical['average_temp_this_day']
            if abs(temp_diff) > 10:
                recommendations.append(
                    f"Note: {temp_diff:+.1f}°F {'warmer' if temp_diff > 0 else 'cooler'} than typical"
                )

        print(f"✓ Generated {len(recommendations)} recommendations")
    else:
        recommendations = ["Unable to generate recommendations due to API errors"]
        print(f"✗ Could not generate recommendations")

    duration = time.time() - start_time

    result = {
        "pattern": "chained_apis",
        "zip_code": zip_code,
        "location_info": location_info,
        "current_weather": {
            "temperature": weather.temperature if weather else None,
            "condition": weather.condition if weather else None
        } if weather else None,
        "historical": historical,
        "recommendations": recommendations,
        "errors": errors if errors else None,
        "duration": duration
    }

    print(f"\n✓ Workflow completed in {duration:.2f}s")
    if errors:
        print(f"⚠️  {len(errors)} error(s) occurred (graceful degradation)")

    return result


# ============================================================================
# Main Demo
# ============================================================================

def main():
    """Run all workflow pattern demonstrations."""

    print("\n" + "="*80)
    print("STORY 7: WORKFLOW ORCHESTRATION WITH EXTERNAL APIs")
    print("="*80)
    print("\nDemonstrating 4 workflow patterns using Agent Framework concepts:")
    print("1. Direct External API (no agent)")
    print("2. Concurrent External APIs")
    print("3. Hybrid (API + optional agent)")
    print("4. Chained APIs with error handling")

    results = {}

    try:
        # Pattern 1: Direct API
        results['pattern_1'] = workflow_pattern_1_direct_api("10001")

        # Pattern 2: Concurrent
        results['pattern_2'] = workflow_pattern_2_concurrent(["10001", "90210", "98101"])

        # Pattern 3: Hybrid (with and without agent)
        results['pattern_3_simple'] = workflow_pattern_3_hybrid("10001", use_agent=False)
        results['pattern_3_enhanced'] = workflow_pattern_3_hybrid("90210", use_agent=True)

        # Pattern 4: Chained
        results['pattern_4'] = workflow_pattern_4_chained("33101")

        # Summary
        print("\n" + "="*80)
        print("SUMMARY: Workflow Pattern Comparison")
        print("="*80)
        print(f"\n{'Pattern':<30} {'Duration':<15} {'Notes'}")
        print("-" * 80)

        print(f"{'1. Direct API':<30} {results['pattern_1']['duration']:<14.2f}s  Simple & fast")
        print(f"{'2. Concurrent (3 locations)':<30} {results['pattern_2']['duration']:<14.2f}s  Parallel execution")
        print(f"{'3. Hybrid (simple)':<30} {results['pattern_3_simple']['duration']:<14.2f}s  Rules only")
        print(f"{'3. Hybrid (enhanced)':<30} {results['pattern_3_enhanced']['duration']:<14.2f}s  With agent")
        print(f"{'4. Chained APIs':<30} {results['pattern_4']['duration']:<14.2f}s  Multiple sources")

        print("\n" + "="*80)
        print("KEY TAKEAWAYS")
        print("="*80)
        print("✅ External APIs can be called directly without agents")
        print("✅ Concurrent execution improves throughput for multiple calls")
        print("✅ Hybrid pattern: use agents only when sophisticated reasoning needed")
        print("✅ Error handling enables graceful degradation")
        print("✅ Workflow orchestration reduces costs vs. agent-only approach")

        # Save results
        with open("workflow-patterns-results.json", 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n✓ Results saved to workflow-patterns-results.json")

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
