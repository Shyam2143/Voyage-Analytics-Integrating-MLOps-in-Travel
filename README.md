# Voyage Analytics: Flight Price Prediction

An end-to-end flight-price regression project with model training, MLflow
experiment tracking, an Airflow workflow, and a Flask prediction API. Run the
stack locally with Docker Compose or deploy the API to Kubernetes.

## Requirements

- Docker Desktop for the full application stack
- Python 3.12 for running training directly
- The flight dataset at `DATA/flights.csv`

Set `FLIGHT_PRICE_DATASET_PATH` to use a different dataset file.

## Run with Docker Compose

From the repository root, start Docker Desktop and run:

```bash
cd "Flight price prediction"
docker compose up --build -d
```

Open the services at:

- Prediction API: <http://localhost:8000>
- Airflow: <http://localhost:8080>
- MLflow: <http://localhost:5001>

Get the generated Airflow standalone credentials with:

```bash
docker compose logs airflow
```

In Airflow, open and trigger the `flight_price_training` DAG. It checks for the
dataset and trains the model to `artifacts/best_flight_price_model.joblib`.
Restart the API after training so it loads the new model:

```bash
docker compose restart flight-price-api
```

Airflow and MLflow data is retained in Docker volumes. Stop the stack without
deleting that data with:

```bash
docker compose down
```

For additional startup notes, see [DOCKER.md](Flight%20price%20prediction/DOCKER.md).

## Run Training Locally

From the repository root, install dependencies, start the Compose MLflow
service, and run the training script:

```bash
cd "Flight price prediction"
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
docker compose up -d mlflow
MLFLOW_TRACKING_URI=http://localhost:5001 python src/train_model.py
```

Training reads `DATA/flights.csv` by default. Without
`MLFLOW_TRACKING_URI`, local runs use `Flight price prediction/mlflow.db`,
separate from the Compose MLflow store. Set the tracking URI as shown above to
view local training runs in the Compose MLflow UI.

## MLflow Contents

The `flight-price-prediction` experiment records a parent training run with
nested runs for baseline and tuned candidates. Runs include model parameters
and regression metrics (MSE, RMSE, MAE, and R-squared). The parent run also
includes cross-validation scores, model comparison CSVs, a sanity-check report,
training logs, and the selected model artifact. Since the target is a
continuous price, the project uses regression metrics rather than a
classification report.

## Kubernetes

The Kubernetes manifests deploy the prediction API image from Docker Hub. See
[KUBERNETES.md](Flight%20price%20prediction/KUBERNETES.md) for deployment,
port-forwarding, scaling, and cleanup commands.

## Project Files

- `DATA/`: input CSV files; training uses `flights.csv` by default
- `Flight price prediction/src/train_model.py`: preprocessing, evaluation, tuning, saving, and MLflow logging
- `Flight price prediction/src/flight_price_api.py`: Flask prediction API and web form
- `Flight price prediction/dags/flight_price_training_dag.py`: Airflow dataset check and training workflow
- `Flight price prediction/artifacts/`: saved model used by the API
- `Flight price prediction/k8s/`: Kubernetes deployment and service manifests
- `Flight price prediction/Flight_Price_Prediction.ipynb`: project notebook