"""
Airflow DAG for Daily Stats Job

Runs daily at end of day (11:59 PM) to compute and send statistics
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'careerops',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 26),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'daily_stats_summary',
    default_args=default_args,
    description='Compute and send daily statistics summary',
    schedule_interval='59 23 * * *',  # Run at 11:59 PM every day
    catchup=False,
    tags=['stats', 'daily', 'notifications'],
)

# Task to run the daily stats job
run_stats_job = BashOperator(
    task_id='compute_and_send_stats',
    bash_command='python /app/deploy/scripts/daily_stats_job.py',
    dag=dag,
)

run_stats_job
