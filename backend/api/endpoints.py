from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any, List
from backend.services.weather_service import WeatherService
from backend.services.decision_engine import DecisionEngine
from backend.config import settings

router = APIRouter(prefix="/api")

# Static configuration of the 6 categories
CATEGORY_CONFIG = [
    {
        "id": "health",
        "name": "Health & Wellness",
        "icon": "🩺",
        "description": "Allergy, asthma & air quality guidance",
        "accent": "emerald"
    },
    {
        "id": "fitness",
        "name": "Outdoor Fitness",
        "icon": "🏃",
        "description": "Find the best time to workout & run",
        "accent": "blue"
    },
    {
        "id": "beach",
        "name": "Beach & Water",
        "icon": "🏖️",
        "description": "Tides, swell, waves & swim safety",
        "accent": "cyan"
    },
    {
        "id": "travel",
        "name": "Travel & Trips",
        "icon": "✈️",
        "description": "Multi-day forecast & smart packing list",
        "accent": "violet"
    },
    {
        "id": "parents",
        "name": "Parents & Families",
        "icon": "👨‍👩‍👧‍👦",
        "description": "School commute alerts & park play windows",
        "accent": "amber"
    },
    {
        "id": "commute",
        "name": "Daily Commute",
        "icon": "🚗",
        "description": "Road safety & rush-hour traffic weather",
        "accent": "rose"
    }
]

@router.get("/location/search")
async def search_location(q: str = Query(..., min_length=2)):
    results = await WeatherService.search_locations(q)
    return {"query": q, "results": results}

@router.get("/weather/current")
async def get_current_weather(
    lat: float = Query(settings.DEFAULT_LAT),
    lon: float = Query(settings.DEFAULT_LON),
    location_name: Optional[str] = Query(settings.DEFAULT_CITY)
):
    try:
        data = await WeatherService.get_comprehensive_weather(lat, lon)
        return {
            "status": "success",
            "location_name": location_name or settings.DEFAULT_CITY,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch weather: {str(e)}")

@router.get("/planning/summary")
async def get_planning_summary(
    lat: float = Query(settings.DEFAULT_LAT),
    lon: float = Query(settings.DEFAULT_LON),
    location_name: Optional[str] = Query(settings.DEFAULT_CITY)
):
    """
    Returns card-level micro-indicators for all 6 categories to populate
    the 2-column mobile category grid on 'Plan for What Matters'.
    """
    weather_data = await WeatherService.get_comprehensive_weather(lat, lon)
    curr = weather_data.get("current", {})

    categories_summary = []
    for cat in CATEGORY_CONFIG:
        cat_id = cat["id"]
        # Determine quick micro indicator string
        if cat_id == "health":
            micro_indicator = f"AQI {curr.get('aqi', 45)} • UV {curr.get('uv_index', 4)}"
            pill_status = "Good" if curr.get("aqi", 45) < 60 else "Moderate"
        elif cat_id == "fitness":
            wind = "Low wind" if curr.get("wind_speed", 10) < 15 else "Breezy"
            micro_indicator = f"{int(curr.get('temperature', 24))}°C • {wind}"
            pill_status = "Optimal"
        elif cat_id == "beach":
            micro_indicator = f"Waves {curr.get('wave_height', 0.8)}m • Waters {int(curr.get('water_temp', 25))}°C"
            pill_status = "Safe" if curr.get("wave_height", 0.8) < 1.2 else "Caution"
        elif cat_id == "travel":
            micro_indicator = f"Rain {curr.get('rain_probability', 20)}% • {curr.get('condition', 'Clear')}"
            pill_status = "Dry Trip" if curr.get("rain_probability", 20) < 30 else "Carry Umbrella"
        elif cat_id == "parents":
            micro_indicator = f"{int(curr.get('temperature', 24))}°C • School Run Clear"
            pill_status = "Kids Safe"
        elif cat_id == "commute":
            micro_indicator = f"Vis {curr.get('visibility_km', 10)} km • Roads Dry"
            pill_status = "Smooth"
        else:
            micro_indicator = f"{int(curr.get('temperature', 24))}°C"
            pill_status = "Normal"

        categories_summary.append({
            **cat,
            "micro_indicator": micro_indicator,
            "status_badge": pill_status
        })

    return {
        "status": "success",
        "location_name": location_name or settings.DEFAULT_CITY,
        "current_weather": curr,
        "categories": categories_summary
    }

@router.get("/planning/category/{category_id}")
async def get_category_dashboard(
    category_id: str,
    lat: float = Query(settings.DEFAULT_LAT),
    lon: float = Query(settings.DEFAULT_LON),
    location_name: Optional[str] = Query(settings.DEFAULT_CITY)
):
    """
    Returns full personalized intelligence dashboard for a selected category.
    """
    valid_ids = [c["id"] for c in CATEGORY_CONFIG]
    if category_id not in valid_ids:
        raise HTTPException(status_code=404, detail=f"Category '{category_id}' not found.")

    weather_data = await WeatherService.get_comprehensive_weather(lat, lon)
    evaluation = DecisionEngine.evaluate_category(category_id, weather_data, location_name or settings.DEFAULT_CITY)

    return {
        "status": "success",
        "location_name": location_name or settings.DEFAULT_CITY,
        "current_weather": weather_data.get("current", {}),
        "evaluation": evaluation,
        "hourly": weather_data.get("hourly", [])[:12],
        "daily": weather_data.get("daily", [])[:7]
    }

@router.get("/planning/travel")
async def get_travel_planning(
    dest_lat: float = Query(...),
    dest_lon: float = Query(...),
    dest_name: str = Query("Destination"),
    origin_name: Optional[str] = Query("Current Location")
):
    """
    Special travel feature: Current Location -> Destination comparison
    with packing generator, multi-day forecast, and travel alerts.
    """
    dest_weather = await WeatherService.get_comprehensive_weather(dest_lat, dest_lon)
    evaluation = DecisionEngine.evaluate_category("travel", dest_weather, dest_name)

    return {
        "status": "success",
        "origin_name": origin_name,
        "dest_name": dest_name,
        "destination_weather": dest_weather.get("current", {}),
        "evaluation": evaluation,
        "daily_forecast": dest_weather.get("daily", [])
    }
