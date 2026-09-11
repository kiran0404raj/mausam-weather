import asyncio
import sys
from backend.services.weather_service import WeatherService
from backend.services.decision_engine import DecisionEngine

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    print("Testing Geocoding...")
    locs = await WeatherService.search_locations("Bengaluru")
    print(f"Found {len(locs)} locations: {[l['label'] for l in locs[:2]]}")
    assert len(locs) > 0, "Location search failed"

    print("\nTesting Comprehensive Weather...")
    w = await WeatherService.get_comprehensive_weather(12.9716, 77.5946)
    print("Current temp:", w['current']['temperature'], "°C")
    print("AQI:", w['current']['aqi'])
    print("Daily forecast days:", len(w['daily']))
    assert 'temperature' in w['current'], "Missing temp"

    print("\nTesting 6 Categories Decision Engine...")
    categories = ["health", "fitness", "beach", "travel", "parents", "commute"]
    for cat in categories:
        eval_result = DecisionEngine.evaluate_category(cat, w, "Bengaluru")
        print(f"[{cat.upper()}] Status: {eval_result['status']} | Headline: {eval_result['headline'][:40]}...")
        assert "headline" in eval_result
        assert "action_recommendation" in eval_result

    print("\nAll Backend Tests Passed Successfully!")

if __name__ == "__main__":
    asyncio.run(main())
