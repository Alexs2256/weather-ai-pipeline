import psycopg2
import time 
import logging
import pytz
from google import genai
from google.genai import types
from pydantic import BaseModel
from google.genai.errors import ServerError,ClientError
from deep_translator import GoogleTranslator
from plugins.weather_pipeline.settings import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

LATEST_ALL_CITIES_SQL = """
    SELECT DISTINCT ON (city)
        city, temperature, humidity, pressure, wind_speed, description, timestamp
    FROM all_city_weather_data
    ORDER BY city, timestamp DESC;
"""

CITY_TIMEZONES = {
"London":   "Europe/London",
"New York": "America/New_York",
"Tokyo":    "Asia/Tokyo",
"Berlin":   "Europe/Berlin",
}

DB_CONFIG = {
    "host":     settings.db_host,
    "dbname":   settings.db_name,
    "user":     settings.db_user,
    "password": settings.db_password,
    "port":     settings.db_port,
}

# --- Pydantic Data Schemas ---
class CityWeatherSummary(BaseModel):
    city: str
    summary: str
    generated_at: str

class WeatherDescription(BaseModel):
    cities: list[CityWeatherSummary]

# --- Core ETL Functions ---

def format_timestamp(ts, timezone_str):
    tz = pytz.timezone(timezone_str)
    if ts.tzinfo is None:
        ts = pytz.utc.localize(ts)
    return ts.astimezone(tz).strftime("%Y-%m-%d %I:%M %p %Z")

def extract_from_postgres() -> list[str]:
    """Fetches raw weather metrics and structures them into text prompts."""
    all_cities = []
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute(LATEST_ALL_CITIES_SQL)
                rows = cursor.fetchall()
                # Note: 'Saved summaries to postgres' log was removed from here 
                # because this is the extraction step, not the load step.   

                for city in rows:
                    metrics=[city[0], city[1], city[2], city[3], city[4], city[5], city[6]]
                    
                    alerts=get_weather_alert(metrics, cursor)

                    tz_str = CITY_TIMEZONES.get(city[0], "UTC")
                    formatted_time = format_timestamp(city[6], tz_str)

                    metrics_context = (
                    f"City: {city[0]}, Temp: {city[1]}°C, "
                    f"Humidity: {city[2]}%, Pressure: {city[3]}hPa, "
                    f"Wind: {city[4]}mph, Description: {city[5]}," 
                    f"Timestamp: {formatted_time},"
                    f"Alerts: {', '.join(alerts) if alerts else 'None'}"
            )

                    all_cities.append(metrics_context)

    except psycopg2.Error as e:
        logger.error("Database extraction error: %s", e)
        raise 

    logger.info("Extracted metrics for %d cities", len(all_cities))
    return all_cities

def get_weather_alert(metrics: list[float], cursor):
    """Checks weather metrics against thresholds and returns any relevant alerts."""
    temp, humidity, pressure, wind_speed = float(metrics[1]), float(metrics[2]), float(metrics[3]), float(metrics[4])
    alerts = []
    
    if temp > 35:
        alerts.append("High temperatures, HEAT WARNING ISSUED")
        if wind_speed >= 20 and humidity <= 25 and temp > 35:
                alerts.append("High winds, low humidity and high temperatures, FIRE WEATHER WARNING ISSUED")
        if humidity > 80:
            alerts.append("Heat stroke is highly likely with any prolonged outdoor exposure, EXTREME HEAT WARNING ISSUED")
    elif temp < 0:
        alerts.append("Freezing temperatures expected, FROST WARNING ISSUED")
        if temp < 0 and wind_speed >= 35:
            alerts.append("Blizzard conditions expected, TRAVEL WARNING ISSUED")
    if humidity > 80:
        alerts.append("High humidity alert, increased risk of heat-related illnesses")
    if wind_speed >= 40:
        alerts.append("High winds expected, POSSIBLE DAMAGE TO TREES AND POWERLINES")

    def get_severe_weather_alert(metrics: list[float]):
        current_pressure = metrics[3]
        query = """
        SELECT city, pressure, timestamp 
        FROM all_city_weather_data
        WHERE city = %s 
          AND timestamp >= NOW() - INTERVAL '3 hours'
        ORDER BY timestamp ASC
        LIMIT 1;
    """
        try:
            cursor.execute(query, (metrics[0],))
            result = cursor.fetchone()
            if result:
                prev_pressure = result[1]
            else: return 
        except psycopg2.Error as e:
            logger.error("Database query error: %s", e)
            return None
        
        if (prev_pressure - current_pressure) >= 3:
            alerts.append('Drastic drop in pressure detected, STORM ALERT ISSUED')

    get_severe_weather_alert(metrics)

    return alerts
  
MODEL_FALLBACKS = ["gemini-2.5-flash", "gemini-2.0-flash-lite"]

def transform_weather_with_gemini(metrics_context: list[str]) -> WeatherDescription:
    """Sends text prompts to Gemini API and forces a structured JSON output."""
    custom_key = settings.gemini_key
    if not custom_key:
        raise ValueError("GEMINI_API_KEY not set in environment")

    client = genai.Client(api_key=custom_key)
    
    for model_name in MODEL_FALLBACKS:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=f"Write a description for this weather data: {metrics_context}",
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=WeatherDescription,
                        system_instruction=(
                        "You are a weather reporter. Write a short, natural description based on the metrics. "
                        "Show temperature in Fahrenheit and Celsius. "
                        "For Berlin, write summary_native in German. For Tokyo, write summary_native in Japanese. "
                        "For all other cities, write summary in English. "
                        "Give any clothing or activity recommendations based on the weather."
                        "If there is a weather alert, prioritize it, state the alert clearly and recommend safety precautions."
    )    
                    )
                )
                return WeatherDescription.model_validate_json(response.text)
            except ServerError as e:
                if e.code == 503 and attempt < 2:
                    wait = 2 ** attempt  
                    logger.warning("Gemini unavailable, retrying in %ss...", wait)
                    time.sleep(wait)
                else:
                    logger.error("Gemini server error after retries: %s", e)
                    break

            except ClientError as e:
                if e.code == 429:
                    logger.warning("Quota exceeded on %s, trying next model", model_name)
                    break  # exit the attempt loop, move to the next model
                logger.error("Gemini client error on %s: %s", model_name, e)
                raise  # non-quota client errors (e.g. bad request) aren't worth retrying on another model
            
    raise RuntimeError("All Gemini model fallbacks exhausted")


def load_back_to_postgres(weather_description: WeatherDescription):
    """Inserts structured LLM summaries back into target PostgreSQL table."""
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS gemini_prompt(
                        city         VARCHAR(100),
                        summary      TEXT,
                        generated_at TIMESTAMP,
                        PRIMARY KEY (city, generated_at)        
                    )
                """)
                for city in weather_description.cities:
                    cursor.execute("""
                        INSERT INTO gemini_prompt (city, summary, generated_at)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (city, generated_at) DO NOTHING
                    """, (city.city, city.summary, city.generated_at))
            conn.commit()
        logger.info("Saved summaries to postgres")
    except psycopg2.Error as e:
        logger.error("Database loading error: %s", e)
        raise


def run_pipeline():
    logger.info("Starting Weather ETL Pipeline...")
    
    # 1. Extract
    raw_metrics = extract_from_postgres()
    if not raw_metrics:
        logger.warning("No metrics found to process.")
        return
        
    # 2. Transform
    structured_json = transform_weather_with_gemini(raw_metrics)
    
    # 3. Load
    load_back_to_postgres(structured_json)
    logger.info("Pipeline completed successfully!")


if __name__ == "__main__":
    run_pipeline()
