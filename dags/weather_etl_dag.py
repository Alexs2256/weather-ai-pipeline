import sys
from pathlib import Path
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from utils.extract import extract_main
from utils.transform import transform_main
from utils.load import load_data_to_postgres
from datetime import datetime, timedelta

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
    schedule_interval='@hourly',
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
    

    extract >> transform >> load
