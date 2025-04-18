from airflow import DAG
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.operators.python import PythonOperator,  BranchPythonOperator
# from airflow.operators.dummy import DummyOperator
# from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta
from src.utils.send_email import send_failure_email, send_success_email
# from src.utils.preprocessing import data_preprocessing
from src.utils.load_jobs import load_jobs
from src.utils.post_gen_helper import generate_posts
from src.logger import logger


POSTING_PATH_BUCKET = 'linkedlens_data/filtered_data/postings.parquet'
BASE_URL = "https://storage.cloud.google.com/linkedlens-airflow-logs/data-generation"

def decide_next(**kwargs):
    file_exists = kwargs['ti'].xcom_pull(task_ids='check_file_exists')
    if file_exists is None:
        file_exists = False
    return "skip_preprocessing" if file_exists else "run_preprocessing"


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
    'owner': 'Apeksha',
    'start_date': datetime(2025, 3, 6),
    'retries': 0, 
    'retry_delay': timedelta(minutes=5), 
}

dag = DAG(
    dag_id='Data_Generation_Pipeline',
    default_args=default_args,
    description='Data_Generation_Pipeline',
    schedule_interval=None,
    catchup=False,
)

# Task: Sensor to check file existence in GCP bucket.
check_file_exists = GCSObjectExistenceSensor(
    task_id="check_file_exists",
    bucket="linkedlens_data",
    object="filtered_data/postings.parquet",
    poke_interval=10,
    timeout=20,
    mode='poke',
    soft_fail=True,
    dag=dag,
)


# Task: Load all job postings.
load_jobs_task = PythonOperator(
    task_id="load_jobs",
    python_callable=load_jobs,
    op_args=[POSTING_PATH_BUCKET, 1000],
    on_success_callback=notify_success,
    on_failure_callback=notify_failure, 
    dag=dag,
)

# Task: Create recruiter posts.
create_recruiter_posts_task = PythonOperator(
    task_id="create_recruiter_posts",
    python_callable=generate_posts,
    # bucket_filepath: str, column_names: List[str], filter: bool, num_rows: int, user_type: str
    op_args=[POSTING_PATH_BUCKET, ["job_id", "description", "title", "company_name"], True, 5000, 'recruiter'],
    on_success_callback=notify_success,
    on_failure_callback=notify_failure,
    dag=dag,
)

# # # Task: Create interview experience posts.
create_interview_exp_posts_task = PythonOperator(
    task_id="create_interview_exp_posts",
    python_callable=generate_posts,
    # bucket_filepath: str, column_names: List[str], filter: bool, num_rows: int, user_type: str
    op_args=[POSTING_PATH_BUCKET, ["job_id", "title", "company_name"], True, 5000, 'user'],
    on_success_callback=notify_success,
    on_failure_callback=notify_failure,
    dag=dag,
)

# Set up task dependencies.
check_file_exists >> load_jobs_task >> create_recruiter_posts_task >> create_interview_exp_posts_task
