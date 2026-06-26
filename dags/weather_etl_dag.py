from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from plugins.weather_pipeline.extract import extract_main
from plugins.weather_pipeline.transform import transform_main
from plugins.weather_pipeline.load import load_data_to_postgres
from plugins.weather_pipeline.weather_prediction import run_pipeline

default_args = {
    "owner": "alex",
    "retries": 1,
    'retry_delay': timedelta(minutes=5)
}

def run_load(**kwargs):
    ti = kwargs['ti']
    clean_data = ti.xcom_pull(task_ids='transform')
    load_data_to_postgres(clean_data)

with DAG(
    dag_id="weather_etl",
    start_date=datetime(2024, 1, 23),
    schedule="0 */2 * * *",
    catchup=False,
    default_args=default_args,

) as dag:
    
    extract = PythonOperator(
        task_id="extract",
        python_callable=extract_main,
    )

    transform = PythonOperator(
        task_id="transform",
        python_callable=transform_main,
    )

    load = PythonOperator(
        task_id="load",
        python_callable=run_load,
    )

    weather_prediction = PythonOperator(
        task_id="weather_prediction",
        python_callable=run_pipeline,
    )


    extract >> transform >> load >> weather_prediction
