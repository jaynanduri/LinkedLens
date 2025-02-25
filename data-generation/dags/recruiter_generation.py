from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta

from src.utils.user_gen_helper import read_input_file, create_company_user_map, user_recruiter_generation
from airflow import configuration as conf

conf.set('core', 'enable_xcom_pickling', 'True')


default_args = {
    'owner': 'Apeksha',
    'start_date': datetime(2025, 1, 15),
    'retries': 0, 
    'retry_delay': timedelta(minutes=5), 
}

dag = DAG(
    'Recruiter_Generator',
    default_args=default_args,
    description='Generate recruiters for companies',
    schedule_interval=None,
    catchup=False,
)

# Task 1 Read input file
load_data_task = PythonOperator(
    task_id='load_input_data',
    python_callable=read_input_file,
    op_args=["linkedlens_processed_data/job_postings/tech_postings.parquet", "company_name"],
    dag=dag,
)

# Task 2 Create company user map
create_company_map = PythonOperator(
    task_id='create_company_user_map',
    python_callable=create_company_user_map,
    op_args=[load_data_task.output, "company_name"],
    dag=dag,
)

# Task 3 User recruiter generation
generate_recruiters = PythonOperator(
    task_id='user_recruiter_generation',
    python_callable=user_recruiter_generation,
    op_args=[create_company_map.output, 'user-recruiter-generation', 'recruiter'],
    dag=dag,
)

# task dependencies
load_data_task >> create_company_map >> generate_recruiters