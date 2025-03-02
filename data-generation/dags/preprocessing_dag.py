from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
from airflow.utils.trigger_rule import TriggerRule
import pandas as pd
from src.utils.send_email import send_failure_email, send_success_email
from src.utils.preprocessing import load_and_clean_data, filter_technology_industry

# Set folders (inside container paths in Airflow)
CLEANED_DATA_DIR_GCS = 'linkedlens_data/processed_data'
FILTERED_DATA_DIR_GCS = 'linkedlens_data/filtered_data'
RAW_DATA_DIR_GCS = 'linkedlens_data/raw_data'


# Default arguments for the DAG
default_args = {
    'owner': 'Ovi',
    'start_date': datetime(2025, 3, 1),
    'retries': 0,
    'retry_delay': timedelta(minutes=5)
}

# Instantiate the DAG
with DAG(
    'Preprocess_Data',
    default_args=default_args,
    description='Preprocess_Data',
    schedule_interval=None,
    catchup=False,
) as dag:

    preprocessing = PythonOperator(
        task_id='preprocessing_task',
        python_callable=load_and_clean_data,
        op_args=[RAW_DATA_DIR_GCS, CLEANED_DATA_DIR_GCS],
        provide_context=True
    )

    filtering = PythonOperator(
        task_id='filtering_task',
        python_callable=filter_technology_industry,
        op_args=[CLEANED_DATA_DIR_GCS, FILTERED_DATA_DIR_GCS],
        provide_context=True
    )

    success_email = PythonOperator(
        task_id='send_success_email',
        python_callable=send_success_email,
        trigger_rule=TriggerRule.ALL_SUCCESS,  
        provide_context = True
    )

    failure_email = PythonOperator(
        task_id='send_failure_email',
        python_callable=send_failure_email,
        trigger_rule=TriggerRule.ONE_FAILED, 
        provide_context = True
    )

    preprocessing >> filtering >> [success_email, failure_email]
