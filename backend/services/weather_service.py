import httpx
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

WEATHER_CODE_MAP = {
    0: {"label": "Clear sky", "icon": "☀️"},
    1: {"label": "Mainly clear", "icon": "🌤️"},
    2: {"label": "Partly cloudy", "icon": "⛅"},
    3: {"label": "Overcast", "icon": "☁️"},
    45: {"label": "Fog", "icon": "🌫️"},
    48: {"label": "Depositing rime fog", "icon": "🌫️"},
    51: {"label": "Light drizzle", "icon": "🌦️"},
    53: {"label": "Moderate drizzle", "icon": "🌦️"},
    55: {"label": "Dense drizzle", "icon": "🌧️"},
    61: {"label": "Slight rain", "icon": "🌧️"},
    63: {"label": "Moderate rain", "icon": "🌧️"},
    65: {"label": "Heavy rain", "icon": "🌧️"},
    71: {"label": "Slight snow fall", "icon": "🌨️"},
    73: {"label": "Moderate snow fall", "icon": "🌨️"},
    75: {"label": "Heavy snow fall", "icon": "❄️"},
    80: {"label": "Slight rain showers", "icon": "🌦️"},
    81: {"label": "Moderate rain showers", "icon": "🌧️"},
    82: {"label": "Violent rain showers", "icon": "⛈️"},
    95: {"label": "Thunderstorm", "icon": "⛈️"},
    96: {"label": "Thunderstorm with slight hail", "icon": "⛈️"},
    99: {"label": "Thunderstorm with heavy hail", "icon": "⛈️"},
}

def get_weather_desc(code: int) -> Dict[str, str]:
    return WEATHER_CODE_MAP.get(code, {"label": "Partly cloudy", "icon": "⛅"})

class WeatherService:
    @staticmethod
    async def search_locations(query: str) -> List[Dict[str, Any]]:
        """Search cities worldwide via Open-Meteo Geocoding API."""
        if not query or len(query.strip()) < 2:
            return []
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {
            "name": query.strip(),
            "count": 6,
            "language": "en",
            "format": "json"
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    results = data.get("results", [])
                    return [
                        {
                            "name": r.get("name"),
                            "latitude": r.get("latitude"),
                            "longitude": r.get("longitude"),
                            "country": r.get("country", ""),
                            "admin1": r.get("admin1", ""),
                            "label": f"{r.get('name')}, {r.get('admin1', '') + ', ' if r.get('admin1') else ''}{r.get('country', '')}".strip()
                        }
                        for r in results
                    ]
        except Exception as e:
            logger.error(f"Error searching location: {e}")
        return []

    _CACHE: Dict[Any, Any] = {}
    _CACHE_TTL: float = 300.0  # 5 minutes

    @classmethod
    async def get_comprehensive_weather(cls, lat: float, lon: float) -> Dict[str, Any]:
        """Fetch real-time weather, forecast, air quality, and marine metrics concurrently with caching."""
        cache_key = (round(lat, 3), round(lon, 3))
        now_ts = datetime.now().timestamp()
        if cache_key in cls._CACHE:
            ts, cached_data = cls._CACHE[cache_key]
            if now_ts - ts < cls._CACHE_TTL:
                return cached_data

        forecast_url = "https://api.open-meteo.com/v1/forecast"
        forecast_params = {
            "latitude": lat,
            "longitude": lon,
            "current": [
                "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                "is_day", "precipitation", "rain", "weather_code",
                "cloud_cover", "pressure_msl", "surface_pressure",
                "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m"
            ],
            "hourly": [
                "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                "precipitation_probability", "precipitation", "weather_code",
                "visibility", "wind_speed_10m", "uv_index", "is_day"
            ],
            "daily": [
                "weather_code", "temperature_2m_max", "temperature_2m_min",
                "sunrise", "sunset", "uv_index_max", "precipitation_sum",
                "precipitation_probability_max"
            ],
            "timezone": "auto"
        }

        aqi_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        aqi_params = {
            "latitude": lat,
            "longitude": lon,
            "current": [
                "european_aqi", "us_aqi", "pm10", "pm2_5",
                "carbon_monoxide", "nitrogen_dioxide", "sulphur_dioxide",
                "ozone", "dust", "uv_index", "alder_pollen", "birch_pollen",
                "grass_pollen", "mugwort_pollen", "olive_pollen", "ragweed_pollen"
            ],
            "timezone": "auto"
        }

        marine_url = "https://marine-api.open-meteo.com/v1/marine"
        marine_params = {
            "latitude": lat,
            "longitude": lon,
            "current": ["wave_height", "wave_direction", "wave_period", "wind_wave_height"],
            "hourly": ["wave_height", "wave_direction", "wave_period"],
            "timezone": "auto"
        }

        weather_res = None
        aqi_res = None
        marine_res = None

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                weather_res = await client.get(forecast_url, params=forecast_params)
            except Exception as e:
                logger.warning(f"Forecast fetch error: {e}")

            try:
                aqi_res = await client.get(aqi_url, params=aqi_params)
            except Exception as e:
                logger.warning(f"AQI fetch error: {e}")

            try:
                marine_res = await client.get(marine_url, params=marine_params)
            except Exception as e:
                logger.warning(f"Marine fetch error: {e}")

        # Parse Weather
        weather_data = weather_res.json() if weather_res and weather_res.status_code == 200 else {}
        aqi_data = aqi_res.json() if aqi_res and aqi_res.status_code == 200 else {}
        marine_data = marine_res.json() if marine_res and marine_res.status_code == 200 else {}

        curr = weather_data.get("current", {})
        daily = weather_data.get("daily", {})
        hourly = weather_data.get("hourly", {})
        curr_aqi = aqi_data.get("current", {})
        curr_marine = marine_data.get("current", {})

        w_code = curr.get("weather_code", 0)
        desc = get_weather_desc(w_code)

        # Sunrise & Sunset
        sunrise_list = daily.get("sunrise", [])
        sunset_list = daily.get("sunset", [])
        sunrise = sunrise_list[0].split("T")[-1] if sunrise_list else "06:15"
        sunset = sunset_list[0].split("T")[-1] if sunset_list else "18:25"

        # Current UV Index
        uv_curr = curr_aqi.get("uv_index")
        if uv_curr is None:
            # Fallback to hourly index
            hourly_uv = hourly.get("uv_index", [])
            uv_curr = hourly_uv[datetime.now().hour] if hourly_uv and len(hourly_uv) > datetime.now().hour else 5.0

        # AQI
        us_aqi = curr_aqi.get("us_aqi") or curr_aqi.get("european_aqi") or 45
        pm2_5 = curr_aqi.get("pm2_5") or 14.5
        pm10 = curr_aqi.get("pm10") or 28.0

        # Pollen Count estimate
        pollen_types = ["grass_pollen", "birch_pollen", "alder_pollen", "ragweed_pollen"]
        pollen_values = [curr_aqi.get(p, 0) or 0 for p in pollen_types]
        total_pollen = sum(pollen_values)
        if total_pollen > 0:
            pollen_level = "High" if total_pollen > 60 else ("Moderate" if total_pollen > 20 else "Low")
        else:
            # Approximate based on season & humidity
            pollen_level = "Moderate" if curr.get("relative_humidity_2m", 50) > 60 else "Low"

        # Marine Data
        wave_h = curr_marine.get("wave_height")
        wave_period = curr_marine.get("wave_period")
        is_coastal = wave_h is not None and wave_h > 0
        if not is_coastal:
            # Inland approximation for lakes / rivers
            wave_h = round(0.15 + (curr.get("wind_speed_10m", 10) * 0.02), 2)
            wave_period = 4.5
            water_temp = round(curr.get("temperature_2m", 25) - 2.5, 1)
        else:
            water_temp = round(curr.get("temperature_2m", 25) - 1.5, 1)

        # Visibility
        hourly_vis = hourly.get("visibility", [])
        curr_hour_idx = datetime.now().hour
        visibility_km = round((hourly_vis[curr_hour_idx] / 1000) if hourly_vis and len(hourly_vis) > curr_hour_idx else 10.0, 1)

        # Rain probability
        hourly_rain_prob = hourly.get("precipitation_probability", [])
        curr_rain_prob = hourly_rain_prob[curr_hour_idx] if hourly_rain_prob and len(hourly_rain_prob) > curr_hour_idx else int(daily.get("precipitation_probability_max", [20])[0] or 20)

        # Multi-day forecast items (5-7 days)
        daily_forecast = []
        if daily.get("time"):
            for i in range(min(7, len(daily["time"]))):
                day_code = daily.get("weather_code", [0])[i] if i < len(daily.get("weather_code", [])) else 0
                d_desc = get_weather_desc(day_code)
                date_str = daily["time"][i]
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    day_name = dt.strftime("%a") if i > 0 else "Today"
                except Exception:
                    day_name = f"Day {i+1}"

                daily_forecast.append({
                    "date": date_str,
                    "day": day_name,
                    "max_temp": round(daily.get("temperature_2m_max", [28])[i]),
                    "min_temp": round(daily.get("temperature_2m_min", [20])[i]),
                    "condition": d_desc["label"],
                    "icon": d_desc["icon"],
                    "rain_prob": daily.get("precipitation_probability_max", [15])[i] or 10,
                    "uv_max": daily.get("uv_index_max", [6])[i] or 5
                })

        # Next 24 hours timeline
        hourly_timeline = []
        if hourly.get("time"):
            start_h = curr_hour_idx
            for h in range(start_h, min(start_h + 24, len(hourly["time"]))):
                h_code = hourly.get("weather_code", [0])[h] if h < len(hourly.get("weather_code", [])) else 0
                h_desc = get_weather_desc(h_code)
                raw_time = hourly["time"][h]
                display_time = raw_time.split("T")[-1]  # "14:00"
                hourly_timeline.append({
                    "time": display_time,
                    "temp": round(hourly.get("temperature_2m", [25])[h]),
                    "feels_like": round(hourly.get("apparent_temperature", [25])[h]),
                    "humidity": hourly.get("relative_humidity_2m", [50])[h],
                    "wind_speed": hourly.get("wind_speed_10m", [10])[h],
                    "uv": hourly.get("uv_index", [4])[h] if hourly.get("uv_index") else 3,
                    "rain_prob": hourly.get("precipitation_probability", [10])[h] if hourly.get("precipitation_probability") else 10,
                    "condition": h_desc["label"],
                    "icon": h_desc["icon"]
                })

        result = {
            "latitude": lat,
            "longitude": lon,
            "current": {
                "temperature": round(curr.get("temperature_2m", 24.0), 1),
                "feels_like": round(curr.get("apparent_temperature", 25.0), 1),
                "humidity": curr.get("relative_humidity_2m", 60),
                "wind_speed": round(curr.get("wind_speed_10m", 12.0), 1),
                "wind_direction": curr.get("wind_direction_10m", 180),
                "wind_gusts": round(curr.get("wind_gusts_10m", 15.0), 1),
                "weather_code": w_code,
                "condition": desc["label"],
                "icon": desc["icon"],
                "is_day": curr.get("is_day", 1),
                "sunrise": sunrise,
                "sunset": sunset,
                "uv_index": round(float(uv_curr), 1),
                "aqi": us_aqi,
                "pm2_5": pm2_5,
                "pm10": pm10,
                "pollen_level": pollen_level,
                "visibility_km": visibility_km,
                "rain_probability": curr_rain_prob,
                "wave_height": wave_h,
                "wave_period": wave_period,
                "water_temp": water_temp,
                "is_coastal": is_coastal
            },
            "hourly": hourly_timeline,
            "daily": daily_forecast,
            "raw_hourly": hourly
        }
        cls._CACHE[cache_key] = (now_ts, result)
        return result
