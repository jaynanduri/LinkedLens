from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from airflow.utils.trigger_rule import TriggerRule
from src.main import load_env
from airflow import configuration as conf

conf.set('core', 'enable_xcom_pickling', 'True')


default_args = {
    'owner': 'Apeksha',
    'start_date': datetime(2025, 1, 15),
    'retries': 0, 
    'retry_delay': timedelta(minutes=5), 
}

dag = DAG(
    'Test_Pipeline',
    default_args=default_args,
    description='Generate recruiters posts',
    schedule_interval=None,
    catchup=False,
)


load_data_task = PythonOperator(
    task_id='load_input_data',
    python_callable=load_env,
    dag=dag,
)
