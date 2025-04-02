from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from src.main import init_pinecone, test_connections, ingest_data
from src.utils.email_util import send_success_email, send_failure_email
from src.utils import logger

import os
os.environ["NO_PROGRESS_BAR"] = "1"

BASE_URL = "https://storage.cloud.google.com/linkedlens-airflow-logs/data-pipeline"

def notify_success(context):
    task_id = context['task_instance'].task_id
    dag_id = context["task_instance"].dag_id 
    execution_date = context['execution_date']
    logger.info(f"Task {task_id} succeeded!")
    send_success_email(dag_id, task_id, execution_date)
    logger.info(f"Task {task_id} succeeded!")

def notify_failure(context):
    dag_id = context["task_instance"].dag_id 
    run_id = context["task_instance"].run_id
    task_id = context["task_instance"].task_id
    attempt = context["task_instance"].try_number
    
    log_url = f"{BASE_URL}/dag_id={dag_id}/run_id={run_id}/task_id={task_id}/attempt={attempt}.log"
    send_failure_email(dag_id, task_id, log_url)
    logger.info(f"Task {task_id} failed! Log URL: {log_url}")


default_args = {
    'owner': 'Akshay',
    'start_date': datetime(2025, 3, 1), 
    'retries': 0, 
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'Update_VectorDB',  # Give your DAG a descriptive name
    default_args=default_args,
    description='Run init, test, and sync steps for your project',
    schedule_interval=None,
    catchup=False,
)

init_task = PythonOperator(
    task_id='initialize_pinecone',
    python_callable=init_pinecone,
    dag=dag,
)

test_task = PythonOperator(
    task_id='test_connections',
    python_callable=test_connections,
    dag=dag,
)

sync_task = PythonOperator(
    task_id='sync_data',
    python_callable=ingest_data,
    op_args=[True],
    on_success_callback=notify_success,
    on_failure_callback=notify_failure,
    dag=dag,
)

# Set task dependencies
init_task >> test_task >> sync_task 