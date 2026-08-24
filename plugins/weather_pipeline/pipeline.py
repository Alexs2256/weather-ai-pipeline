from .extract import extract_from_postgres # or extract_main
from .transform import transform_weather_with_gemini # or transform_main
from .load import load_back_to_postgres # or load_main

def run_pipeline():
    # If your scripts are built to run sequentially:
    raw_data = extract_from_postgres()
    clean_data = transform_weather_with_gemini(raw_data)
    load_back_to_postgres(clean_data)

if __name__ == "__main__":
    run_pipeline()