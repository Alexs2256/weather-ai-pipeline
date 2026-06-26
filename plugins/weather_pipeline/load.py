import logging
import psycopg2
from pathlib import Path
from plugins.weather_pipeline.settings import settings

logger = logging.getLogger(__name__)

# 1. Dynamically find the project root
# Path(__file__) is this current file; .parent.parent moves up to the project folder
BASE_DIR = Path(__file__).resolve().parent.parent.parent
csv_path = BASE_DIR / "data" / "cleaned_df.csv"

DB_CONFIG = {
    "host":     settings.db_host,
    "dbname":   settings.db_name,
    "user":     settings.db_user,
    "password": settings.db_password,
    "port":     settings.db_port,
}

def load_data_to_postgres(dataFrame):
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cursor:       
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS all_city_weather_data (
                    city VARCHAR(100),
                    temperature FLOAT,
                    humidity INT,
                    pressure INT,
                    wind_speed FLOAT,
                    description VARCHAR(500),
                    timestamp TIMESTAMP,
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
    logger.info("Data loaded successfully")


