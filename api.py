import logging
from pathlib import Path
import psycopg2
from fastapi import FastAPI, HTTPException
from plugins.weather_pipeline.settings import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Weather Pipeline API")

DB_CONFIG = {
    "host":     settings.db_host,
    "dbname":   settings.db_name,
    "user":     settings.db_user,
    "password": settings.db_password,
    "port":     settings.db_port,
}

LATEST_ALL_CITIES_SQL = """
    SELECT DISTINCT ON (city)
        city, temperature, humidity, pressure, wind_speed, timestamp
    FROM all_city_weather_data
    ORDER BY city, timestamp DESC;
"""

LATEST_SUMMARIES_SQL = """
    SELECT DISTINCT ON (city)
        city, summary
    FROM gemini_prompt
    ORDER BY city, generated_at DESC;
"""


@app.get("/weather")
def get_all_weather():
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute(LATEST_ALL_CITIES_SQL)
                rows = cursor.fetchall()

        city_weather_list = []

        for row in rows:
          city_data = {
                "city":        row[0],
                "temperature": row[1],
                "humidity":    row[2],
                "pressure":    row[3],
                "wind_speed":  row[4],
                "timestamp":   str(row[5]),
            }
          
          city_weather_list.append(city_data) 

        return city_weather_list   
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/weather/{city}")
def get_city_weather(city: str):
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute(LATEST_ALL_CITIES_SQL)
                rows = cursor.fetchall()
        for row in rows:
            if row[0] == city:
                city_data = {
                    "city":        row[0],
                    "temperature": row[1],
                    "humidity":    row[2],
                    "pressure":    row[3],
                    "wind_speed":  row[4],
                    "timestamp":   str(row[5]),
                }
                return city_data
        raise HTTPException(status_code=404, detail=f"City '{row[0]}' not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/weather/{city}/summary")  
def get_city_summary(city: str):
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute(LATEST_SUMMARIES_SQL)
                rows = cursor.fetchall()
        for row in rows:
            if row[0] == city:
                summary_data = {
                    "city": row[0],
                    "summary": row[1]
                }
                return summary_data
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
