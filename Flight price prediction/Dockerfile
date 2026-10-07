# The model was developed with Python 3.12, so use the same Python version.
FROM python:3.12-slim

WORKDIR /app

# Keep the image small and make application logs visible in `docker logs`.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install dependencies before copying application files. Docker can reuse this
# layer when only the application code or model changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Keep application code separate from the persisted model artifact.
COPY src/ ./src/
COPY artifacts/ ./artifacts/
ENV FLIGHT_PRICE_MODEL_PATH=/app/artifacts/best_flight_price_model.joblib

EXPOSE 8000

# Docker uses this endpoint to determine whether the service is ready.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

# Gunicorn is a production WSGI server. It imports the Flask app from src.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--timeout", "120", "src.flight_price_api:app"]
