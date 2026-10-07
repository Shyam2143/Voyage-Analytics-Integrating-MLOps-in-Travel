# Flight Price Prediction

A flight-price regression service with model training, experiment tracking, and a Flask prediction API. The training workflow compares baseline regressors, runs cross-validation and hyperparameter searches, then saves a tuned Random Forest model.

## Requirements

- Docker Desktop for the full application stack
- Python 3.12 for running training directly
- The flight dataset at `../DATA/flights.csv` relative to this project directory

Set `FLIGHT_PRICE_DATASET_PATH` to use a different dataset file.

## Run with Docker

From this directory, start the stack:

```bash
docker compose up --build -d
```

Open the services at:

- Prediction API: <http://localhost:8000>
- Airflow: <http://localhost:8080>
- MLflow: <http://localhost:5001>

Find the generated Airflow standalone credentials with:

```bash
docker compose logs airflow
```

In Airflow, open the `flight_price_training` DAG and trigger it. The DAG checks for the dataset and trains the model. The saved model is written to `artifacts/best_flight_price_model.joblib`. Restart the API after a new model is trained so it loads that file:

```bash
docker compose restart flight-price-api
```

The Airflow and MLflow data is retained in Docker volumes. Stop the stack without deleting its data with:

```bash
docker compose down
```

## Run Training Locally

Install the dependencies, start the MLflow service, then run training with the Compose tracking server URI:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
docker compose up -d mlflow
MLFLOW_TRACKING_URI=http://localhost:5001 python src/train_model.py
```

The default dataset path is `../DATA/flights.csv`. Local runs without `MLFLOW_TRACKING_URI` use `mlflow.db` in this directory, which is separate from the Compose MLflow store. To view local runs in the Compose UI, set the tracking URI as shown above.

## MLflow Contents

The `flight-price-prediction` experiment records one parent training run and nested runs for baseline and tuned candidates. Runs include model parameters and regression metrics (MSE, RMSE, MAE, and R-squared). The parent run also includes cross-validation scores, model comparison CSVs, a sanity-check report, captured training logs, and the selected model artifact.

This predicts a continuous price, so regression metrics are used instead of a classification report.

## Project Layout

- `src/train_model.py`: preprocessing, evaluation, hyperparameter tuning, saving, and MLflow logging
- `src/flight_price_api.py`: Flask prediction API and web form
- `dags/flight_price_training_dag.py`: Airflow dataset check and training workflow
- `artifacts/`: saved model used by the API
- `docker-compose.yml`: API, Airflow, and MLflow services
- `DOCKER.md`: additional Docker startup notes
