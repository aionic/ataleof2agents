"""
FastAPI server for the Weather API service.

Simple API that calls OpenWeatherMap and returns weather data.
"""

import os
import logging
from fastapi import FastAPI, HTTPException, Query
from weather_service import WeatherService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Weather API Service",
    description="Simple weather data API using OpenWeatherMap",
    version="1.0.0"
)

# Initialize weather service
weather_service = None

@app.on_event("startup")
async def startup():
    """Initialize weather service on startup."""
    global weather_service
    logger.info("Initializing weather service...")
    weather_service = WeatherService()
    logger.info("Weather service initialized")

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "weather-api"
    }

@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "service": "weather-api",
        "api_key_configured": bool(os.getenv("OPENWEATHERMAP_API_KEY"))
    }

@app.get("/api/weather")
async def get_weather(
    zip_code: str = Query(..., description="5-digit US zip code", regex="^\\d{5}$")
):
    """
    Get weather data for a US zip code.

    Args:
        zip_code: 5-digit US zip code

    Returns:
        Weather data including temperature, conditions, humidity, wind, and precipitation
    """
    if not weather_service:
        logger.error("Weather service not initialized")
        raise HTTPException(status_code=503, detail="Service not available")

    try:
        logger.info(f"Getting weather for zip code: {zip_code}")
        weather_data = weather_service.get_weather(zip_code)
        return weather_data
    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error getting weather for {zip_code}")
        raise HTTPException(status_code=500, detail=f"Error fetching weather data: {str(e)}")
