from typing import Dict, Any, List
from datetime import datetime

class DecisionEngine:
    """
    Rule-based intelligence engine that transforms raw meteorological variables
    into human-centric, actionable guidance, safety indicators, and optimal windows.
    """

    @classmethod
    def evaluate_category(cls, category_id: str, weather_data: Dict[str, Any], location_name: str = "Your Location") -> Dict[str, Any]:
        evaluators = {
            "health": cls._eval_health,
            "fitness": cls._eval_fitness,
            "beach": cls._eval_beach,
            "travel": cls._eval_travel,
            "parents": cls._eval_parents,
            "commute": cls._eval_commute
        }
        fn = evaluators.get(category_id, cls._eval_health)
        return fn(weather_data, location_name)

    @staticmethod
    def _eval_health(data: Dict[str, Any], location: str) -> Dict[str, Any]:
        curr = data.get("current", {})
        aqi = curr.get("aqi", 45)
        uv = curr.get("uv_index", 4.0)
        humidity = curr.get("humidity", 55)
        temp = curr.get("temperature", 25.0)
        pollen = curr.get("pollen_level", "Moderate")

        # Health status calculation
        if aqi > 150 or uv > 9 or temp > 38:
            status = "Poor"
            status_color = "danger"
            headline = "⚠️ Unfavorable Outdoor Health Conditions"
            action = "Limit prolonged outdoor exertion. Sensitive groups and individuals with asthma or allergies should stay indoors with filtered air."
        elif aqi > 100 or uv > 7 or humidity > 85 or temp > 33:
            status = "Moderate"
            status_color = "warning"
            headline = "⚡ Moderate Health Alert"
            action = "Acceptable conditions for general public. Individuals with skin sensitivity or respiratory concerns should apply SPF 50+ and monitor breathing."
        else:
            status = "Good"
            status_color = "success"
            headline = "🌿 Ideal Health & Fresh Air Window"
            action = "Air quality and ambient conditions are clean. Excellent time for brisk walking, jogging, and outdoor wellness."

        # Allergy & Asthma guidance
        allergy_alerts = []
        if pollen == "High":
            allergy_alerts.append("Elevated pollen count detected: keep windows closed and consider taking antihistamines if prone to seasonal rhinitis.")
        if aqi > 100:
            allergy_alerts.append("Elevated particulate matter (PM2.5): asthma inhalers should be kept handy.")
        if humidity > 80:
            allergy_alerts.append("High humidity may exacerbate joint stiffness or heavy breathing.")
        elif humidity < 30:
            allergy_alerts.append("Dry air alert: hydrate frequently and moisturize to prevent skin irritation.")
        if uv >= 6:
            allergy_alerts.append(f"UV index is {uv} (High): apply broad-spectrum sunscreen and wear sunglasses.")

        if not allergy_alerts:
            allergy_alerts.append("No significant environmental allergens or irritants active right now.")

        return {
            "id": "health",
            "name": "Health & Wellness",
            "icon": "🩺",
            "location": location,
            "status": status,
            "status_color": status_color,
            "headline": headline,
            "action_recommendation": action,
            "primary_metric": {"label": "Air Quality Index", "value": f"{aqi} AQI", "subtext": f"US EPA Scale • {status}"},
            "metrics": [
                {"label": "AQI", "value": str(aqi), "badge": status, "icon": "🫁"},
                {"label": "Pollen Count", "value": pollen, "badge": "Allergens", "icon": "🌸"},
                {"label": "UV Index", "value": f"{uv} / 11", "badge": "High" if uv >= 6 else "Safe", "icon": "☀️"},
                {"label": "Humidity", "value": f"{humidity}%", "badge": "Muggy" if humidity > 75 else "Optimal", "icon": "💧"},
                {"label": "Temperature", "value": f"{temp}°C", "badge": "Ambient", "icon": "🌡️"}
            ],
            "guidance_list": allergy_alerts,
            "best_window": "Early morning (6:00 AM – 8:30 AM) when pollutants and ozone settle lowest."
        }

    @staticmethod
    def _eval_fitness(data: Dict[str, Any], location: str) -> Dict[str, Any]:
        curr = data.get("current", {})
        temp = curr.get("temperature", 24.0)
        feels_like = curr.get("feels_like", 25.0)
        humidity = curr.get("humidity", 60)
        wind = curr.get("wind_speed", 10.0)
        uv = curr.get("uv_index", 4.0)
        sunrise = curr.get("sunrise", "06:15")
        sunset = curr.get("sunset", "18:25")
        rain_prob = curr.get("rain_probability", 15)

        # Heat and intensity evaluation
        if temp > 34 or feels_like > 37:
            status = "Caution"
            status_color = "danger"
            heat_alert = "🔥 High Heat & Thermal Stress: Avoid strenuous outdoor training. Shift workouts indoors."
            best_recommendation = "Postpone runs until after sunset when surface heat radiates away."
        elif rain_prob > 60:
            status = "Caution"
            status_color = "warning"
            heat_alert = "🌧️ Slippery Terrain Alert: High chance of wet pavement and reduced traction."
            best_recommendation = "Opt for gravel trails or treadmill sessions today."
        elif uv > 7:
            status = "Moderate"
            status_color = "warning"
            heat_alert = "☀️ High Solar Radiation: Wear protective caps, sunglasses, and hydrate with electrolytes."
            best_recommendation = "Stick to shaded routes and conclude workouts before midday."
        else:
            status = "Good"
            status_color = "success"
            heat_alert = "✨ Prime Fitness Weather: Comfortable ambient temp and low thermal strain."
            best_recommendation = "Optimal conditions for interval training, endurance running, or outdoor calisthenics."

        # Generate "Best Time to Run" timeline based on hourly forecast
        hourly = data.get("hourly", [])
        timeline = []
        for item in hourly[:12]:
            h_temp = item.get("temp", 24)
            h_uv = item.get("uv", 3)
            h_rain = item.get("rain_prob", 10)

            if h_rain > 50 or h_temp > 33:
                h_rating = "Avoid"
                h_badge = "danger"
            elif h_temp > 28 or h_uv > 6:
                h_rating = "Moderate"
                h_badge = "warning"
            else:
                h_rating = "Excellent"
                h_badge = "success"

            timeline.append({
                "time": item.get("time"),
                "temp": f"{h_temp}°C",
                "condition": item.get("condition"),
                "rating": h_rating,
                "badge": h_badge,
                "reason": f"UV {h_uv} • Rain {h_rain}%"
            })

        return {
            "id": "fitness",
            "name": "Outdoor Fitness",
            "icon": "🏃",
            "location": location,
            "status": status,
            "status_color": status_color,
            "headline": heat_alert,
            "action_recommendation": best_recommendation,
            "primary_metric": {"label": "Thermal Comfort", "value": f"{feels_like}°C Feels Like", "subtext": f"Actual {temp}°C • Humidity {humidity}%"},
            "metrics": [
                {"label": "Current Temp", "value": f"{temp}°C", "badge": "Ambient", "icon": "🌡️"},
                {"label": "Feels Like", "value": f"{feels_like}°C", "badge": "Perceived", "icon": "🔥"},
                {"label": "Sunrise / Sunset", "value": f"{sunrise} / {sunset}", "badge": "Daylight", "icon": "🌅"},
                {"label": "Wind Speed", "value": f"{wind} km/h", "badge": "Gentle" if wind < 15 else "Breezy", "icon": "💨"},
                {"label": "UV Index", "value": str(uv), "badge": "High" if uv >= 6 else "Safe", "icon": "☀️"},
                {"label": "Rain Risk", "value": f"{rain_prob}%", "badge": "Slick Road" if rain_prob > 40 else "Dry", "icon": "🌧️"}
            ],
            "timeline": timeline,
            "best_window": f"Early Morning (6:00 AM – 8:00 AM) or Post-Sunset ({sunset} onward)"
        }

    @staticmethod
    def _eval_beach(data: Dict[str, Any], location: str) -> Dict[str, Any]:
        curr = data.get("current", {})
        wave_h = curr.get("wave_height", 0.8)
        wave_p = curr.get("wave_period", 7.5)
        wind = curr.get("wind_speed", 14.0)
        water_temp = curr.get("water_temp", 26.0)
        uv = curr.get("uv_index", 6.0)
        is_coastal = curr.get("is_coastal", False)

        # Sea condition and safety
        if wave_h > 1.8 or wind > 35:
            sea_condition = "Rough & Choppy"
            safety_status = "Unsafe"
            status_color = "danger"
            alert = "🚩 High Surf & Rip Current Risk: Strong offshore gusts and elevated wave height make swimming hazardous."
            best_window = "Avoid open water activities. Wait for calmer morning tide."
        elif wave_h > 1.0 or wind > 22 or uv > 8:
            sea_condition = "Moderate Swell"
            safety_status = "Caution"
            status_color = "warning"
            alert = "🟡 Moderate Water Motion: Safe for experienced swimmers close to shore. Watch for changing tide currents."
            best_window = "Best watersports window: 7:30 AM – 10:30 AM before onshore winds pick up."
        else:
            sea_condition = "Calm & Placid"
            safety_status = "Safe"
            status_color = "success"
            alert = "🟢 Excellent Coastal Conditions: Low surf, crystal water clarity, and gentle breezes."
            best_window = "Ideal beach time throughout mid-morning and late afternoon."

        # Simulated dynamic tide timeline
        tide_timeline = [
            {"time": "05:40 AM", "type": "Low Tide", "height": "0.38 m", "badge": "info"},
            {"time": "11:50 AM", "type": "High Tide", "height": "1.42 m", "badge": "primary"},
            {"time": "05:55 PM", "type": "Low Tide", "height": "0.41 m", "badge": "info"},
            {"time": "11:35 PM", "type": "High Tide", "height": "1.38 m", "badge": "primary"}
        ]

        return {
            "id": "beach",
            "name": "Beach & Water Activities",
            "icon": "🏖️",
            "location": location,
            "status": safety_status,
            "status_color": status_color,
            "headline": alert,
            "action_recommendation": best_window,
            "primary_metric": {"label": "Sea State", "value": sea_condition, "subtext": f"Waves {wave_h}m • Waters {water_temp}°C"},
            "metrics": [
                {"label": "Wave Height", "value": f"{wave_h} m", "badge": "Surf", "icon": "🌊"},
                {"label": "Wave Period", "value": f"{wave_p} s", "badge": "Swell", "icon": "⏱️"},
                {"label": "Water Temp", "value": f"{water_temp}°C", "badge": "Pleasant", "icon": "🏊"},
                {"label": "Wind Speed", "value": f"{wind} km/h", "badge": "Breeze", "icon": "💨"},
                {"label": "UV Radiation", "value": f"{uv} / 11", "badge": "Water Reflective", "icon": "☀️"},
                {"label": "Coastal Zone", "value": "Direct Coast" if is_coastal else "Inland Waterway", "badge": "Zone", "icon": "⚓"}
            ],
            "tide_timeline": tide_timeline,
            "best_window": "Morning low tide window (7:00 AM – 10:30 AM) for swimming and paddleboarding."
        }

    @staticmethod
    def _eval_travel(data: Dict[str, Any], location: str) -> Dict[str, Any]:
        curr = data.get("current", {})
        daily = data.get("daily", [])
        temp = curr.get("temperature", 26.0)
        rain_prob = curr.get("rain_probability", 20)
        wind = curr.get("wind_speed", 12.0)
        vis = curr.get("visibility_km", 10.0)

        # Weather warnings for transit/flight
        warnings = []
        if vis < 3.0:
            warnings.append("Foggy conditions may cause airport ground delays or slow highway traffic.")
        if wind > 40:
            warnings.append("High wind shear alerts in effect: turbulence likely for regional flights.")
        if rain_prob > 60:
            warnings.append("Heavy rain expected: pack waterproof baggage coverings and check flight gate alerts.")
        if not warnings:
            warnings.append("Smooth travel conditions with clear flight corridors and dry roads.")

        # Smart packing generator
        packing = []
        if rain_prob > 35:
            packing.extend(["Compact travel umbrella", "Waterproof hooded jacket", "Water-resistant footwear"])
        if temp > 30:
            packing.extend(["Breathable lightweight cottons", "UV polarized sunglasses", "Sunscreen SPF 50+"])
        elif temp < 16:
            packing.extend(["Thermal fleece or woolen layer", "Windproof jacket", "Light scarf"])
        else:
            packing.extend(["Layerable casual outfits", "Light jacket for evenings"])
        packing.append("Portable power bank & hydration bottle")

        status = "Caution" if (rain_prob > 65 or vis < 4.0 or wind > 35) else "Good"
        status_color = "danger" if status == "Caution" else "success"

        return {
            "id": "travel",
            "name": "Travel & Exploration",
            "icon": "✈️",
            "location": location,
            "status": status,
            "status_color": status_color,
            "headline": f"Destination Forecast for {location}",
            "action_recommendation": f"Pack: {', '.join(packing[:4])}.",
            "primary_metric": {"label": "Travel Weather Readiness", "value": f"{temp}°C • {curr.get('condition')}", "subtext": f"Rain Risk {rain_prob}% • Visibility {vis} km"},
            "metrics": [
                {"label": "Destination Temp", "value": f"{temp}°C", "badge": "Current", "icon": "🌡️"},
                {"label": "Rain Probability", "value": f"{rain_prob}%", "badge": "Precipitation", "icon": "🌧️"},
                {"label": "Transit Visibility", "value": f"{vis} km", "badge": "Clear" if vis > 6 else "Hazy", "icon": "👁️"},
                {"label": "Wind Factor", "value": f"{wind} km/h", "badge": "Cruising", "icon": "💨"}
            ],
            "packing_suggestions": packing,
            "travel_warnings": warnings,
            "multi_day_forecast": daily,
            "best_window": "Safe transit window throughout the daylight hours."
        }

    @staticmethod
    def _eval_parents(data: Dict[str, Any], location: str) -> Dict[str, Any]:
        curr = data.get("current", {})
        hourly = data.get("hourly", [])
        temp = curr.get("temperature", 25.0)
        rain_prob = curr.get("rain_probability", 20)
        vis = curr.get("visibility_km", 9.0)

        # Commute slots: Morning school (07:00-09:00), Afternoon pickup (13:00-15:00), Evening play (17:00-19:00)
        slots = [
            {"slot": "Morning Commute", "hours": "07:30 – 08:45 AM", "icon": "🎒"},
            {"slot": "Afternoon Pickup", "hours": "01:30 – 03:00 PM", "icon": "🚌"},
            {"slot": "Evening Park Play", "hours": "05:00 – 06:45 PM", "icon": "🪁"}
        ]

        commute_cards = []
        for i, slot in enumerate(slots):
            # Pick representative forecast from hourly
            sample_idx = min(i * 3 + 1, len(hourly) - 1) if hourly else 0
            sample = hourly[sample_idx] if hourly else {}
            s_temp = sample.get("temp", temp)
            s_rain = sample.get("rain_prob", rain_prob)
            s_uv = sample.get("uv", 4)

            if s_rain > 50:
                s_status = "Rain Gear Needed"
                s_badge = "danger"
                s_advice = "Pack raincoat in schoolbag; school vans will experience delays."
            elif s_temp > 33 or s_uv > 7:
                s_status = "High Heat"
                s_badge = "warning"
                s_advice = "Pack insulated cold water flask; avoid outdoor recess play."
            else:
                s_status = "Pleasant"
                s_badge = "success"
                s_advice = "Great condition for school commute and open-air games."

            commute_cards.append({
                "title": slot["slot"],
                "hours": slot["hours"],
                "icon": slot["icon"],
                "temp": f"{s_temp}°C",
                "status": s_status,
                "badge": s_badge,
                "rain_prob": f"{s_rain}%",
                "advice": s_advice
            })

        heavy_rain_commute = any("danger" in c["badge"] for c in commute_cards)
        headline = "🌧️ Heavy Rain Expected During Commute" if heavy_rain_commute else "🌤️ Family-Friendly Day Ahead"
        action = "Allow 20 minutes buffer for school runs and equip children with hooded jackets." if heavy_rain_commute else "All clear for school buses, walking routes, and playground activities."

        return {
            "id": "parents",
            "name": "Parents & Families",
            "icon": "👨‍👩‍👧‍👦",
            "location": location,
            "status": "Caution" if heavy_rain_commute else "Good",
            "status_color": "danger" if heavy_rain_commute else "success",
            "headline": headline,
            "action_recommendation": action,
            "primary_metric": {"label": "School Run Feasibility", "value": "Normal Transit" if not heavy_rain_commute else "Weather Delay Likely", "subtext": f"Visibility {vis} km • Rain Risk {rain_prob}%"},
            "metrics": [
                {"label": "Air Temperature", "value": f"{temp}°C", "badge": "Kids Comfort", "icon": "🌡️"},
                {"label": "Rain Risk", "value": f"{rain_prob}%", "badge": "Umbrella" if rain_prob > 30 else "Clear", "icon": "🌧️"},
                {"label": "Commute Visibility", "value": f"{vis} km", "badge": "Driver Sight", "icon": "👁️"},
                {"label": "Playground Status", "value": "Open & Dry" if rain_prob < 30 else "Wet Grounds", "badge": "Parks", "icon": "⚽"}
            ],
            "commute_slots": commute_cards,
            "best_window": "Late afternoon (4:45 PM – 6:30 PM) is optimal for outdoor park play."
        }

    @staticmethod
    def _eval_commute(data: Dict[str, Any], location: str) -> Dict[str, Any]:
        curr = data.get("current", {})
        hourly = data.get("hourly", [])
        temp = curr.get("temperature", 25.0)
        feels_like = curr.get("feels_like", 26.0)
        wind = curr.get("wind_speed", 14.0)
        vis = curr.get("visibility_km", 9.5)
        uv = curr.get("uv_index", 5.0)
        rain_prob = curr.get("rain_probability", 25)

        # Road safety warning calculation
        if vis < 2.0:
            safety_warning = "⚠️ Dense Fog Warning: Severe road visibility reduction. Use low-beam headlights and increase following distance."
            road_status = "Hazardous"
            status_color = "danger"
        elif rain_prob > 60:
            safety_warning = "🌧️ Wet Asphalt & Reduced Grip: Hydroplaning risk on arterial expressways. Leave 15–20 minutes early."
            road_status = "Wet & Slow"
            status_color = "warning"
        elif wind > 35:
            safety_warning = "💨 Crosswind Warning: Two-wheelers and high-sided vehicles should exercise caution on elevated flyovers."
            road_status = "Breezy"
            status_color = "warning"
        else:
            safety_warning = "🚗 Clear & Safe Road Conditions: Good driving visibility, dry tarmac, and predictable transit times."
            road_status = "Optimal"
            status_color = "success"

        # 3 Key Commute Periods
        periods = [
            {"period": "Morning Rush", "hours": "08:00 – 10:30 AM", "icon": "🌅", "rain": f"{rain_prob}%", "status": "Clear" if rain_prob < 40 else "Rainy"},
            {"period": "Midday Transit", "hours": "12:00 – 02:30 PM", "icon": "☀️", "rain": f"{max(5, rain_prob - 10)}%", "status": "Warm & Sunny"},
            {"period": "Evening Return", "hours": "05:30 – 08:30 PM", "icon": "🌆", "rain": f"{min(90, rain_prob + 10)}%", "status": "Smooth" if rain_prob < 50 else "Slow Traffic"}
        ]

        return {
            "id": "commute",
            "name": "Daily Commute & Outdoor Plans",
            "icon": "🚗",
            "location": location,
            "status": road_status,
            "status_color": status_color,
            "headline": safety_warning,
            "action_recommendation": "Optimal departure time is before 8:15 AM or after 10:00 AM to avoid peak congestion combined with weather friction.",
            "primary_metric": {"label": "Commute Friction Index", "value": road_status, "subtext": f"Visibility {vis} km • Wind {wind} km/h"},
            "metrics": [
                {"label": "Current Weather", "value": curr.get("condition", "Clear"), "badge": "Sky", "icon": curr.get("icon", "🌤️")},
                {"label": "Temperature", "value": f"{temp}°C", "badge": f"Feels {feels_like}°", "icon": "🌡️"},
                {"label": "Rain Probability", "value": f"{rain_prob}%", "badge": "Road Surface", "icon": "🌧️"},
                {"label": "Visibility", "value": f"{vis} km", "badge": "Sightline", "icon": "👁️"},
                {"label": "Wind Gusts", "value": f"{wind} km/h", "badge": "Stability", "icon": "💨"},
                {"label": "UV Radiation", "value": f"{uv}", "badge": "In-Car Glare", "icon": "☀️"}
            ],
            "commute_periods": periods,
            "best_window": "Best departure window: 07:45 – 08:15 AM before traffic and temperature peak."
        }
