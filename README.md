# 🌤️ Weather AI Pipeline

An automated weather data pipeline that fetches live weather data for global cities, generates AI-powered summaries using Google Gemini, detects severe weather alerts, and exposes the data through a REST API and interactive dashboard.

---

## 🏗️ Architecture

```
OpenWeatherMap API
       │
       ▼
  [Extract] ──► Raw weather data (temp, humidity, pressure, wind, precipitation)
       │
       ▼
  [Transform] ──► Clean & structure data, detect weather conditions
       │
       ▼
  [Load] ──► PostgreSQL (all_city_weather_data)
       │
       ▼
  [Gemini LLM] ──► AI-generated multilingual summaries ──► PostgreSQL (gemini_prompt)
       │
       ├──► FastAPI  ──► REST endpoints (/weather, /weather/{city}, /weather/{city}/summary)
       │
       └──► Streamlit Dashboard ──► Live weather cards, alerts, multilingual TTS
```

Orchestrated end-to-end by **Apache Airflow** on an hourly schedule.

---

## ✨ Features

- **ETL Pipeline** — Extracts live weather data from OpenWeatherMap for London, New York, Tokyo, and Berlin
- **AI Summaries** — Google Gemini generates natural language weather reports, written in the local language first then translated to English
- **Weather Alert System** — Multi-signal detection for heat, frost, blizzard, fire weather, high winds, humidity, and storm conditions
- **Storm Detection** — Pressure drop analysis over 3-hour historical windows to detect incoming storms
- **FastAPI REST API** — Three endpoints to query current weather and AI summaries programmatically
- **Streamlit Dashboard** — Live weather cards with country flags, condition icons, and alert banners
- **Multilingual TTS** — Browser-based text-to-speech reads summaries in Japanese (Tokyo), German (Berlin), British English (London), and American English (New York)
- **Docker** — PostgreSQL runs in a Docker container for easy setup

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | Apache Airflow |
| Data Source | OpenWeatherMap API |
| Database | PostgreSQL (Docker) |
| LLM | Google Gemini 2.5 Flash |
| API | FastAPI + Uvicorn |
| Dashboard | Streamlit |
| Language | Python 3.10 |
| Packaging | pyproject.toml |

---

## 📁 Project Structure

```
weather-ai-pipeline/
├── dags/
│   └── weather_etl_dag.py       # Airflow DAG definition
├── plugins/
│   └── weather_pipeline/
│       ├── extract.py           # Fetches data from OpenWeatherMap
│       ├── transform.py         # Cleans and structures data
│       ├── load.py              # Loads data into PostgreSQL
│       ├── weather_prediction.py # Gemini LLM summaries + alert logic
│       └── settings.py          # Environment variable config
├── api.py                       # FastAPI REST API
├── dashboard.py                 # Streamlit dashboard
├── pyproject.toml
├── requirements.txt
└── .env.example
```

---

## ⚙️ Setup

### Prerequisites
- Python 3.10+
- Docker
- Apache Airflow
- OpenWeatherMap API key (free at [openweathermap.org](https://openweathermap.org))
- Google Gemini API key (free at [aistudio.google.com](https://aistudio.google.com))

### 1. Clone the repo
```bash
git clone https://github.com/Alexs2256/weather-ai-pipeline.git
cd weather-ai-pipeline
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
pip install -e .
```

### 4. Set up environment variables
```bash
cp .env.example .env
```
Fill in your `.env`:
```
API_KEY=your_openweathermap_api_key
GEMINI_KEY=your_gemini_api_key
DB_HOST=localhost
DB_NAME=weather_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_PORT=5432
```

### 5. Start PostgreSQL with Docker
```bash
docker run --name postgres-weather \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=weather_db \
  -p 5432:5432 \
  -d postgres
```

### 6. Set up Airflow
```bash
export AIRFLOW_HOME=$(pwd)
airflow db init
airflow users create \
  --username admin --password admin \
  --firstname Admin --lastname User \
  --role Admin --email admin@example.com
airflow scheduler &
airflow webserver &
```

### 7. Run the pipeline
Trigger the `weather_etl` DAG from the Airflow UI at `http://localhost:8080`

### 8. Start the API
```bash
uvicorn api:app --reload
```

### 9. Start the dashboard
```bash
streamlit run dashboard.py
```

---

## 🔌 API Endpoints

Base URL: `http://127.0.0.1:8000`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/weather` | Current weather for all cities |
| GET | `/weather/{city}` | Current weather for a specific city |
| GET | `/weather/{city}/summary` | Gemini AI summary for a specific city |

Interactive docs available at: `http://127.0.0.1:8000/docs`

### Example Response — `/weather/London`
```json
{
  "city": "London",
  "temperature": 18.5,
  "humidity": 72,
  "pressure": 1015,
  "wind_speed": 4.47,
  "timestamp": "2026-06-24 20:00:07"
}
```

---

## 🚨 Weather Alert System

Alerts are generated automatically based on metric thresholds:

| Alert | Condition |
|---|---|
| 🔴 Heat Warning | Temp > 35°C |
| 🔴 Fire Weather Warning | Temp > 35°C + Wind > 20mph + Humidity < 25% |
| 🔴 Blizzard Warning | Temp < 0°C + Wind > 35mph |
| 🟠 Frost Warning | Temp < 0°C |
| 🟠 High Wind Warning | Wind > 40mph |
| 🔴 Storm Alert | Pressure drop ≥ 3hPa over 3 hours |
| 🔵 High Humidity Alert | Humidity > 80% |

---

## 📸 Screenshots

### Dashboard
![Dashboard](screenshots/dashboard.png)

### API Docs
![API](screenshots/api.png)
