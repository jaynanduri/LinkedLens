from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from airflow.utils.trigger_rule import TriggerRule

# Import your email functions
# You'll need to create these functions in your src directory
from src.utils.email_util import send_success_email, send_failure_email

default_args = {
    'owner': 'YourName',  # Change to your name
    'start_date': datetime(2025, 3, 1),  # Update to a relevant start date
    'retries': 0,  # You can adjust this if you want retries
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'Your_Project_Pipeline',  # Give your DAG a descriptive name
    default_args=default_args,
    description='Run init, test, and sync steps for your project',
    schedule_interval=None,  # Set to None for manual triggers or adjust as needed
    catchup=False,
)

# Task 1: Init step
init_task = BashOperator(
    task_id='init_step',
    bash_command='python src/main.py init',
    dag=dag,
)

# Task 2: Test step
test_task = BashOperator(
    task_id='test_step',
    bash_command='python src/main.py test',
    dag=dag,
)

# Task 3: Sync step
sync_task = BashOperator(
    task_id='sync_step',
    bash_command='python src/main.py sync',
    dag=dag,
)

# Success email notification
success_email = PythonOperator(
    task_id='send_success_email',
    python_callable=send_success_email,
    trigger_rule=TriggerRule.ALL_SUCCESS,
    provide_context=True,
    dag=dag
)

# Failure email notification
failure_email = PythonOperator(
    task_id='send_failure_email',
    python_callable=send_failure_email,
    trigger_rule=TriggerRule.ONE_FAILED,
    provide_context=True,
    dag=dag
)

# Set task dependencies
init_task >> test_task >> sync_task >> [success_email, failure_email]