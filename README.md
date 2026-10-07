# Voyage-Analytics-Integrating-MLOps-in-Travel

Flight-price prediction project with a Flask API, Airflow training workflow,
Docker Compose setup, and Kubernetes manifests.

## Project layout

- `DATA/` contains the source CSV files. Flight training reads `DATA/flights.csv`.
- `Flight price prediction/src/` contains the API and model-training code.
- `Flight price prediction/dags/` contains the Airflow DAG.
- `Flight price prediction/artifacts/` contains the trained model shared by
	training and the API.
- `Flight price prediction/k8s/` contains Kubernetes manifests.

The training script derives its local dataset path from the project location.
Compose mounts the same repository `DATA/` directory read-only at `/opt/DATA`
and writes the model to the shared `artifacts/` directory.

See [DOCKER.md](Flight%20price%20prediction/DOCKER.md) for running the API and
Airflow locally, and [KUBERNETES.md](Flight%20price%20prediction/KUBERNETES.md)
for Kubernetes deployment instructions.