# Run the app and Airflow with Docker

You only need Docker Desktop installed and running.

## Start the app

Open a terminal in the `Flight price prediction` folder and run:

```bash
docker compose up --build
```

The first run takes longer because Docker downloads the API and Airflow images
and installs their dependencies. Later runs are faster.

When you see `Listening at: http://0.0.0.0:8000`, open this in your browser:

<http://localhost:8000>

Airflow's web UI is available at <http://localhost:8080>. To find the generated
standalone login, run `docker compose logs airflow` and look for the admin
username and password. Open the `flight_price_training` DAG and trigger it to
check the dataset and train the model. Airflow writes the trained model into
`artifacts/best_flight_price_model.joblib`; restart the API container after
training so it loads the new model:

```bash
docker compose restart flight-price-api
```

This single-container Airflow standalone setup is intended for local development,
not production.

## Stop the app

Go back to the terminal and press `Ctrl + C`.

## Start it in the background (optional)

Use this only when you do not want to keep the terminal open:

```bash
docker compose up --build -d
```

To stop a background app later:

```bash
docker compose down
```

You do not need to run the Python file manually. Docker starts the app and
includes the trained model automatically.
