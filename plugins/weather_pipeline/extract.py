import json
import requests
from pathlib import Path
from datetime import datetime, timezone
from plugins.weather_pipeline.settings import settings

#sudo docker start postgres-weather

API_KEY = settings.api_key

if not API_KEY:
    raise ValueError("API_KEY not set in environment")

CITY_NAME = ["London", "New York", "Tokyo", "Berlin"]  # Example cities

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

file_path_data = DATA_DIR / "weather_raw.jsonl"

def get_weather_data(city, api_key):
    base_url = "http://api.openweathermap.org/data/2.5/weather"

    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric'  # Get temperature in Celsius
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)

        response.raise_for_status()
        data = response.json()
        data["_extracted_at"] = datetime.now(timezone.utc).isoformat()
        return data
    
    except requests.RequestException as e:
        print(f"Failed to fetch data for {city}: {e}")
        return None
    
def extract_main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(file_path_data, 'w') as f:
        for city in CITY_NAME:
            raw_data = get_weather_data(city, API_KEY)
            print(raw_data)
            if raw_data:
                # This line guarantees double quotes are used:
                json_string = json.dumps(raw_data)
                f.write(json_string + '\n')
