# 🌤️ Weather AI Pipeline

[![Live Demo](https://img.shields.io/badge/Streamlit-Live%20Demo-red?style=for-the-badge&logo=streamlit)](https://weather-ai-pipeline-qhr9ghvc5zcefnmgqyuz7p.streamlit.app/)

An automated weather data pipeline that fetches live weather data for global cities, generates AI-powered summaries using Google Gemini, detects severe weather alerts, and exposes the data through a REST API and interactive dashboard, orchestrated with Apache Airflow and deployed on AWS EC2 with Docker Compose.

---

## 🏗️ Architecture

<img width="1408" height="768" alt="Weather AI Data Pipeline Architecture" src="https://github.com/user-attachments/assets/443444ef-ac10-4c13-af74-d59dd629ccd0" />

Orchestrated end-to-end by **Apache Airflow** and scheduled every 2 hours via a containerized AWS EC2 Linux setup connecting to a managed PostgreSQL database (Neon).

---

## ✨ Features

- **ETL Pipeline & AI Summaries:** Gathers live data from OpenWeatherMap for major cities and produces translated, Pydantic-validated reports using Google Gemini.
- **Alert & Storm Detection:** Real-time multi-signal evaluation for extreme heat, frost, blizzards, fire weather, high winds, humidity, and 3-hour pressure-drop storm tracking.
- **APIs & Dashboards:** Built-in FastAPI REST endpoints, a Streamlit live dashboard with alert banners, and browser-based multilingual Text-to-Speech (TTS).

---

## 🛠️ Tech Stack & Structure

*   **Orchestration & Backend:** Apache Airflow, Python 3.10, FastAPI, Uvicorn, Pydantic.
*   **Data & AI:** OpenWeatherMap API, Google Gemini 2.5 Flash, PostgreSQL (Docker/Neon).
*   **Deployment:** AWS EC2, Docker Compose, Streamlit.

Core repository layout includes `dags/weather_etl_dag.py`, modular extraction/transformation plugins, FastAPI (`api.py`), and the Streamlit interface (`dashboard.py`).

---

## ⚙️ Local Setup & Deployment

1.  **Clone & Environment:** Clone the repository, create a Python 3.10 virtual environment, and install dependencies via `requirements.txt` and `pip install -e .`.
2.  **Configuration:** Copy `.env.example` to `.env` and configure your OpenWeatherMap API key, Gemini API key, and PostgreSQL credentials.
3.  **Services & Execution:** Launch PostgreSQL via Docker, initialize Apache Airflow (`admin/admin` for local testing), start the Airflow scheduler/webserver, and trigger the `weather_etl` DAG at `http://localhost:8080`.
4.  **Run Interfaces:** Start the FastAPI server using `uvicorn api:app --reload` and launch the dashboard with `streamlit run dashboard.py`.
5.  **AWS EC2 Production:** For cloud deployments, provision a Linux EC2 instance, populate your environment variables pointing `DB_HOST` to a managed database like Neon, and spin up services using `docker compose up -d`. Ensure security groups restrict public exposure of the Airflow UI.

---

## 🔌 API Endpoints & Alert Thresholds

*   **API Base URL (`http://127.0.0.1:8000`):** Access `/weather` (all cities), `/weather/{city}` (specific city), and `/weather/{city}/summary` (AI-generated reports), with interactive documentation available at `/docs`.
*   **Alert Rules:** Triggers automated warnings for Heat (>35°C), Extreme Heat (>35°C + >80% humidity), Fire Weather, Blizzards, Frost, High Winds (>40mph), High Humidity, and Storms (≥3 hPa pressure drop over 3 hours).

---

## 📸 Demo

| Airflow DAG | 🔴 Heat Warning Example |
|---|---|
| [![Airflow DAG Demo](https://img.youtube.com/vi/k_4H9EL21I4/maxresdefault.jpg)](https://www.youtube.com/watch?v=k_4H9EL21I4) | [![Heat Warning Example](https://img.youtube.com/vi/kU50Ca5e394/0.jpg)](https://www.youtube.com/watch?v=kU50Ca5e394) |
