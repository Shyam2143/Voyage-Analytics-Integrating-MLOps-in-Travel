# Voyage Analytics: Flight Price Prediction

An end-to-end flight-price regression project with model training, MLflow
experiment tracking, an Airflow workflow, and a Flask prediction API. Run the
stack locally with Docker Compose or deploy the API to Kubernetes.

## Quick start

Install and start Docker Desktop, then run these commands from the repository
root:

```bash
cd "Flight price prediction"
docker compose up --build -d
```

Open the prediction app at <http://localhost:8000>, Airflow at
<http://localhost:8080>, or MLflow at <http://localhost:5001>. For Airflow's
generated standalone login, run `docker compose logs airflow` from the project
directory.

## Project files

- `DATA/` contains the input CSV files. Training uses `flights.csv` by default.
- `Flight price prediction/src/` contains the training code and Flask API.
- `Flight price prediction/dags/` contains the Airflow training workflow.
- `Flight price prediction/artifacts/` contains the model shared by training
	and the API.
- `Flight price prediction/k8s/` contains the Kubernetes deployment and service.
- `Flight price prediction/Flight_Price_Prediction.ipynb` contains the project
	notebook.

Training reads `DATA/flights.csv` by default. Set
`FLIGHT_PRICE_DATASET_PATH` to use a different file. Docker Compose mounts the
repository's `DATA/` directory read-only for Airflow and shares the `artifacts/`
directory with the API.

## Guides

- [Flight price prediction project guide](Flight%20price%20prediction/README.md)
- [Run with Docker Compose](Flight%20price%20prediction/DOCKER.md)
- [Deploy to Kubernetes](Flight%20price%20prediction/KUBERNETES.md)