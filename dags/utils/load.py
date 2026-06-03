import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.types import String, Float, Integer, DateTime  # Added imports


# 1. Dynamically find the project root
# Path(__file__) is this current file; .parent.parent moves up to the project folder
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"
csv_path = BASE_DIR / "data" / "cleaned_df.csv"

load_dotenv(dotenv_path=env_path)

def load_data_to_postgres(dataFrame):
    conn = psycopg2.connect(
        host=os.getenv("host"),
        database=os.getenv("database"),
        user=os.getenv("user"),
        password=os.getenv("password"),
        port=os.getenv("port")
    )
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS all_city_weather_data (
            city VARCHAR(100) UNIQUE,
            temperature FLOAT,
            humidity INT,
            pressure INT,
            wind_speed FLOAT,
            description VARCHAR(500),
            timestamp TIMESTAMP UNIQUE,
            PRIMARY KEY (city, timestamp) 
            )
    """)

    for i, record in dataFrame.iterrows():
        cursor.execute("""
            INSERT INTO all_city_weather_data (city, temperature, humidity, pressure, wind_speed, description, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (city, timestamp) DO NOTHING
        """, (
            record['city'],
            record['temperature'],
            record['humidity'],
            record['pressure'],
            record['wind_speed'],
            record['description'],
            record['timestamp']
        ))

    conn.commit()
    cursor.close()
    conn.close()
    print("Data loaded successfully")


