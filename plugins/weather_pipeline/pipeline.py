from extract import extract_main
from transform import transform_main
from load import load_data_to_postgres

def run_pipeline():
    raw_data = extract_main()
    clean_data = transform_main()
    load_data_to_postgres(clean_data)

if __name__ == "__main__":
    run_pipeline()