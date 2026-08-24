import json
import os
import pandas as pd
from pathlib import Path
from datetime import datetime

# 1. Dynamically find the project root
# Path(__file__) is this current file; .parent.parent moves up to the project folder
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

file_path_clean_df = DATA_DIR / "cleaned_df.csv" 
file_path_data = DATA_DIR / "weather_raw.jsonl"

def create_data_frame(raw_data):
    if not raw_data:
        return None

    new_data_list = []
    print(raw_data[0]['name'])

    for i in range(len(raw_data)):
        """We extract the appropriate fields from raw_data and inserting 
        the results into a dictionary names new_row. Once all of the fields 
        are taken and inserted into new_row for the current iteration, we append 
        the dictionary into the new_data_list"""

        city = raw_data[i]['name']
        temp = raw_data[i]['main']['temp']
        humidity = raw_data[i]['main']['humidity']
        pressure = raw_data[i]['main']['pressure']
        wind_speed = raw_data[i]['wind']['speed']
        description = raw_data[i]['weather'][0]['description']
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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

    return df


def convert_datatypes(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def drop_na(df):
    df_cleaned = df.dropna().copy()
    return df_cleaned

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
        print(f"Error: {file_path_data} not found.")
        exit()
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        exit()

    weather_dataframe = create_data_frame((all_weather_records))

    # Convert to appropriate data types for each column and drop empty rows
    cleaned_df = convert_datatypes(weather_dataframe)
    cleaned_df = drop_na(cleaned_df)
    cleaned_df.to_csv(file_path_clean_df, index=False)


if __name__ == "__main__":
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
        print(f"Error: {file_path_data} not found.")
        exit()
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        exit()

    weather_dataframe = create_data_frame((all_weather_records))

    # Convert to appropriate data types for each column and drop empty rows
    cleaned_df = convert_datatypes(weather_dataframe)
    cleaned_df = drop_na(cleaned_df)

    print(cleaned_df.head())
    print(cleaned_df.dtypes)

    # Check to see if there are any missing values
    print(cleaned_df.isnull().sum())

    if os.path.exists(file_path_clean_df):
        os.remove(file_path_clean_df)
        print(f"""File '{file_path_clean_df}' found and deleted.
              Made room for new file""")

    cleaned_df.to_csv(file_path_clean_df, index=False)

    #load_data_frame = load_data_to_postgres(cleaned_df)
