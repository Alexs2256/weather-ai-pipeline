import json
import os
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

# 1. Dynamically find the project root
# Path(__file__) is this current file; .parent.parent moves up to the project folder
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

file_path_clean_df = DATA_DIR / "cleaned_df.csv" 
file_path_data = DATA_DIR / "weather_raw.jsonl"

def create_data_frame(raw_data):
    """We extract the appropriate fields from raw_data and inserting 
        the results into a dictionary names new_row. Once all of the fields 
        are taken and inserted into new_row for the current iteration, we append 
        the dictionary into the new_data_list"""
    if not raw_data:
        return None

    new_data_list = []

    for data_record in raw_data:
        city = data_record['name']
        temp = data_record['main']['temp']
        humidity = data_record['main']['humidity']
        pressure = data_record['main']['pressure']
        wind_speed = data_record['wind']['speed']
        description = data_record['weather'][0]['description']
        # Use the timestamp from extraction instead
        timestamp = data_record.get('_extracted_at', datetime.now(timezone.utc).isoformat())

        # Create a pandas DataFrame
        new_row = {
            'city': city,
            'temperature': temp,
            'humidity': humidity,
            'pressure': pressure,
            'wind_speed': wind_speed,
            'description': description,
            'timestamp': timestamp
        }

        new_data_list.append(new_row)

    df = pd.DataFrame(new_data_list)

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.dropna().copy()

    return df

def transform_main():
    all_weather_records = []
    try:
        with open(file_path_data, 'r') as f:
            # Iterate over every line in the file
            for line in f:
                clean_line = line.strip()
                if clean_line:
                    # Load THIS SINGLE LINE as a Python dictionary
                    record = json.loads(clean_line)
                    all_weather_records.append(record)

    except FileNotFoundError:
        raise FileNotFoundError(f"{file_path_data} not found.")
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding JSON: {e}")

    weather_dataframe = create_data_frame(all_weather_records)
    #weather_dataframe.to_csv(file_path_clean_df, index=False)

    print(weather_dataframe.head())
    print(weather_dataframe.dtypes)
    # Check to see if there are any missing values
    print(weather_dataframe.isnull().sum())

    return weather_dataframe



