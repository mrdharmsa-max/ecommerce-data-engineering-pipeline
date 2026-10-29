
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


with DAG(
    dag_id="ecommerce_postgres_etl",
    description="Run the ecommerce PostgreSQL incremental ETL pipeline",
    start_date=datetime(2026, 10, 1),
    schedule="0 8 * * *",
    catchup=False,
    tags=["ecommerce", "postgres", "etl"],
) as dag:

    run_etl = BashOperator(
        task_id="run_incremental_etl",
        bash_command=(
            "cd /opt/airflow/project && "
            "python src/postgres_pipeline.py"
        ),
    )
