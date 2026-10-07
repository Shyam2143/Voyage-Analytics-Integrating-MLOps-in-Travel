"""Airflow orchestration for flight-price model training."""

import sys
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
if str(PROJECT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIRECTORY))

from src.train_model import check_dataset, train_model


with DAG(
    dag_id="flight_price_training",
    description="Check the flight dataset and train the flight-price regression model",
    start_date=datetime(2024, 1, 1),
    schedule="@weekly",
    catchup=False,
    tags=["flight-price", "machine-learning", "training"],
) as dag:
    check_dataset_task = PythonOperator(
        task_id="check_dataset",
        python_callable=check_dataset,
    )

    train_model_task = PythonOperator(
        task_id="train_model",
        python_callable=train_model,
    )

    check_dataset_task >> train_model_task