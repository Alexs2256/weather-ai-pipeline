import logging
import psycopg2
import pytz
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from deep_translator import GoogleTranslator
from plugins.weather_pipeline.settings import settings
from plugins.weather_pipeline.weather_prediction import get_weather_alert

#source ~/airflow_venv/bin/activate
#streamlit run projects/DataEngineerProj1/dashboard.py

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host":     settings.db_host,
    "dbname":   settings.db_name,
    "user":     settings.db_user,
    "password": settings.db_password,
    "port":     settings.db_port,
}

LATEST_ALL_CITIES_SQL = """
    SELECT DISTINCT ON (city)
        city, temperature, humidity, pressure, wind_speed, description, timestamp
    FROM all_city_weather_data
    ORDER BY city, timestamp DESC;
"""

LATEST_SUMMARIES_SQL = """
    SELECT DISTINCT ON (city)
        city, summary
    FROM gemini_prompt
    ORDER BY city, generated_at DESC;
"""

@st.cache_data(ttl=600)
def fetch_latest_records() -> list[dict]:
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cursor:
            cursor.execute(LATEST_ALL_CITIES_SQL)
            rows = cursor.fetchall()
    return [
        {
            "city":        row[0],
            "temperature": row[1],
            "humidity":    row[2],
            "pressure":    row[3],
            "wind_speed":  row[4],
            "description": row[5],
            "timestamp":   row[6],
        }
        for row in rows
    ]


@st.cache_data(ttl=600)
def get_all_summaries() -> dict[str, str]:
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cursor:
            cursor.execute(LATEST_SUMMARIES_SQL)
            rows = cursor.fetchall()
    return {row[0]: row[1] for row in rows}

def format_timestamp(ts, timezone_str):
    tz = pytz.timezone(timezone_str)
    if ts.tzinfo is None:
        ts = pytz.utc.localize(ts)
    return ts.astimezone(tz).strftime("%Y-%m-%d %I:%M %p %Z")

def speak_summary(text: str, city: str):
    """Renders a TTS button using the browser's built-in speechSynthesis API."""
    # Strip markdown bold markers so they aren't read aloud

    if city == 'Tokyo' or city == 'Berlin':
        foreign_clean_text = text[0].replace("**", "").replace("`", "'")
        clean_text = text[1].replace("**", "").replace("`", "'")
    else:
        foreign_clean_text = ""
        clean_text = text.replace("**", "").replace("`", "'")
    
    components.html(f"""
        <button onclick="
            window.speechSynthesis.cancel();
            if ('{city}' == 'Tokyo') {{
            var u = new SpeechSynthesisUtterance(`{foreign_clean_text}`);
            u.lang = 'ja-JP';  // Japanese
            window.speechSynthesis.speak(u);
            }}
            else if ('{city}' == 'Berlin') {{
            var u = new SpeechSynthesisUtterance(`{foreign_clean_text}`);
            u.lang = 'de-DE'; // German
            window.speechSynthesis.speak(u);
            }}
            var u = new SpeechSynthesisUtterance(`{clean_text}`);
            window.speechSynthesis.speak(u);
            
        "
            style="background:#1f77b4; color:white; border:none; padding:8px 16px;
                   border-radius:8px; cursor:pointer; font-size:14px; margin-right:8px;">
            🔊 Read {city} Summary
        </button>
        <button onclick="window.speechSynthesis.cancel();"
            style="background:#555; color:white; border:none; padding:8px 16px;
                   border-radius:8px; cursor:pointer; font-size:14px;">
            ⏹ Stop
        </button>
    """, height=50)


def render_city_card(record: dict, summaries: dict[str, str], cursor):
    city = record["city"]

    flags = {
        "London":   "https://flagcdn.com/w40/gb.png",
        "New York": "https://flagcdn.com/w40/us.png",
        "Tokyo":    "https://flagcdn.com/w40/jp.png",
        "Berlin":   "https://flagcdn.com/w40/de.png",
    }
    flag_url = flags.get(city, "")

    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
            <img src="{flag_url}" style="height: 28px; border-radius: 3px;">
            <h2 style="margin: 0; color: white; font-family: Arial, sans-serif;">{city}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns(4)
    fahrenheit = round(record['temperature'] * 9/5 + 32, 2)
    col1.metric("🌡️ Temperature", f"{record['temperature']}°C / {fahrenheit}°F")
    col2.metric("💧 Humidity",    f"{record['humidity']}%")
    col3.metric("🔵 Pressure",    f"{record['pressure']} hPa")
    col4.metric("💨 Wind Speed",  f"{record['wind_speed']} mph")

    rain_col, _ = st.columns([1, 3])
    
    weather_description = record["description"]

    if "thunderstorm" in weather_description.lower():
        rain_col.metric("⛈️ Thunderstorm", f"{record['description']}")
    elif "snow" in weather_description.lower() or "sleet" in weather_description.lower():
        rain_col.metric("🌨️ Snowfall", f"{record['description']}")
    elif "drizzle" in weather_description.lower():
        rain_col.metric("🌦️ Drizzle", f"{record['description']}")
    elif "rain" in weather_description.lower():
        rain_col.metric("🌧️ Rainfall", f"{record['description']}")
    elif "fog" in weather_description.lower() or "mist" in weather_description.lower():
        rain_col.metric("🌫️ Fog", f"{record['description']}")
    elif "cloud" in weather_description.lower():
        rain_col.metric("☁️ Cloudy", f"{record['description']}")
    elif weather_description == "clear sky":
        rain_col.metric("☀️ Clear Sky", f"{record['description']}")
    else:
        rain_col.metric("🌤️", f"{record['description']}")
    
    CITY_TIMEZONES = {
    "London":   "Europe/London",
    "New York": "America/New_York",
    "Tokyo":    "Asia/Tokyo",
    "Berlin":   "Europe/Berlin",
}

    tz_str = CITY_TIMEZONES.get(city, "UTC")
    formatted_time = format_timestamp(record['timestamp'], tz_str)
    st.caption(f"Last updated: {formatted_time}")

    # --- Weather Alerts ---
    
    alerts = get_weather_alert([
        city,
        record["temperature"],
        record["humidity"],
        record["pressure"],
        record["wind_speed"],
        record["timestamp"],
    ], cursor)

    if alerts:
        for alert in alerts:
            if any(k in alert for k in ("STORM", "BLIZZARD", "FIRE")):
                st.error(f"🔴 {alert}")
            elif "WARNING" in alert:
                st.warning(f"🟠 {alert}")
            else:
                st.info(f"🔵 {alert}")

    summary = summaries.get(city, "No summary available.")

    if city == 'Tokyo' or city == 'Berlin':
        summary = summary  + ' English Translation: ' + GoogleTranslator(source='auto', target='en').translate(summaries.get(city, "No summary available."))
                                    

    st.markdown(
        f"""
        <div style="
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            color: #000000;
            font-size: 15px;
            font-family: Georgia, serif;
            line-height: 1.6;
        ">
            {summary}

        </div>
        """,
        unsafe_allow_html=True
    )

    if city == 'Tokyo' or city == 'Berlin':
        summary = summary.split(' English Translation: ')

    speak_summary(summary, city)
    st.divider()

def main():
    st.set_page_config(page_title="Weather Dashboard", page_icon="🌤️", layout="wide")
    st.title("🌤️ Global Weather Dashboard")
    st.caption("Live conditions powered by OpenWeatherMap + Gemini")

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()

    try:
        records = fetch_latest_records()
        summaries = get_all_summaries()
    except Exception as e:
        st.error(f"Failed to load weather data: {e}")
        return

    if not records:
        st.warning("No data found. Run the pipeline first.")
        return
    
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cursor:
            for record in records:
                render_city_card(record, summaries, cursor)


if __name__ == "__main__":
    main()
