import requests
import json
import os
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
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

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data: {response.status_code}")
        return None
    
def extract_main():
    raw_data = ""
    #Remove old file to makeway for new data
    #if os.path.exists(file_path_data):
        #os.remove(file_path_data)
    with open(file_path_data, 'w') as f:
        for city in CITY_NAME:
            raw_data = get_weather_data(city, API_KEY)
            if raw_data:
                # This line guarantees double quotes are used:
                json_string = json.dumps(raw_data)
                f.write(json_string + '\n')


if __name__ == "__main__":
    raw_data = ""
    #Remove old file to makeway for new data
    #if os.path.exists(file_path_data):
        #os.remove(file_path_data)
    with open(file_path_data, 'w') as f:
        for city in CITY_NAME:
            raw_data = get_weather_data(city, API_KEY)
            print(raw_data)
            if raw_data:
                # This line guarantees double quotes are used:
                json_string = json.dumps(raw_data)
                f.write(json_string + '\n')
