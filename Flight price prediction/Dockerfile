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

# Only these two files are needed at runtime.
COPY flight_price_api.py best_flight_price_model.joblib ./

EXPOSE 8000

# Docker uses this endpoint to determine whether the service is ready.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

# Gunicorn is a production WSGI server. It imports `app` from flight_price_api.py.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--timeout", "120", "flight_price_api:app"]
