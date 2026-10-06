# Run the app with Docker

You only need Docker Desktop installed and running.

## Start the app

Open a terminal in the `Flight price prediction` folder and run:

```bash
docker compose up --build
```

The first run takes a little longer because Docker downloads Python and installs
the libraries. Later runs are faster.

When you see `Listening at: http://0.0.0.0:8000`, open this in your browser:

<http://localhost:8000>

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
