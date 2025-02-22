from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta

import sys
import os

# print(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.utils.user_gen_helper import read_input_file, create_company_user_map, connect_to_db, get_request_limiter, get_llm_chain, user_recruiter_generation
from airflow import configuration as conf



# Enable pickle support for XCom, allowing data to be passed between tasks
conf.set('core', 'enable_xcom_pickling', 'True')

# Define default arguments for your DAG
default_args = {
    'owner': 'Apeksha',
    'start_date': datetime(2025, 1, 15),
    'retries': 0, # Number of retries in case of task failure
    'retry_delay': timedelta(minutes=5), # Delay before retries
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
    op_args=[""],
    dag=dag,
)

# Task 2 Create company user map
create_company_map = PythonOperator(
    task_id='create_company_user_map',
    python_callable=create_company_user_map,
    op_args=[load_data_task.output],
    dag=dag,
)

# # Task 3 Connect to DB
# get_db_client = PythonOperator(
#     task_id='connect_to_db',
#     python_callable=connect_to_db,
#     dag=dag,
# )

# # Task 4 Get Request limiter
# request_limiter = PythonOperator(
#     task_id='get_request_limiter',
#     python_callable=get_request_limiter,
#     dag=dag,
# )

# # Task 5 Get LLM chain
# llm_chain = PythonOperator(
#     task_id='get_llm_chain',
#     python_callable=get_llm_chain,
#     op_args=['user-recruiter-generation'],
#     dag=dag,
# )

# Task 6 User recruiter generation
generate_recruiters = PythonOperator(
    task_id='user_recruiter_generation',
    python_callable=user_recruiter_generation,
    op_args=[create_company_map.output, 'user-recruiter-generation', 'recruiter'],
    dag=dag,
)

# task dependencies
load_data_task >> create_company_map >> generate_recruiters