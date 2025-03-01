from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from airflow.utils.trigger_rule import TriggerRule


from src.utils.post_gen_helper import create_hiring_posts
from src.utils.gen_helper import read_input_file
from src.utils.send_email import send_failure_email, send_success_email
from airflow import configuration as conf

conf.set('core', 'enable_xcom_pickling', 'True')


default_args = {
    'owner': 'Apeksha',
    'start_date': datetime(2025, 1, 15),
    'retries': 0, 
    'retry_delay': timedelta(minutes=5), 
}

dag = DAG(
    'Recruiter_Post_Generator',
    default_args=default_args,
    description='Generate recruiters posts',
    schedule_interval=None,
    catchup=False,
)

# Task 1 Read input file
load_data_task = PythonOperator(
    task_id='load_input_data',
    python_callable=read_input_file,
    op_args=["linkedlens_processed_data/job_postings/tech_postings.parquet", ["job_id", "description", "title", "company_name"]],
    dag=dag,
)

# Task 2 Create recruiter posts
create_posts = PythonOperator(
    task_id='create_hiring_posts',
    python_callable=create_hiring_posts,
    op_args=[load_data_task.output, "recruiter-post"],
    dag=dag,
)

success_email = PythonOperator(
    task_id='send_success_email',
    python_callable=send_success_email,
    trigger_rule=TriggerRule.ALL_SUCCESS, 
    provide_context = True,
    dag=dag
)

failure_email = PythonOperator(
    task_id='send_failure_email',
    python_callable=send_failure_email,
    trigger_rule=TriggerRule.ONE_FAILED,  
    provide_context = True,
    dag=dag
)

# task dependencies
load_data_task >> create_posts >> [success_email, failure_email]