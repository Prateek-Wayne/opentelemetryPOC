FROM python:3.11.3-slim
WORKDIR /worker

# Environment variables for Celery
ENV CELERY_BROKER_URL pyamqp://guest:guest@rabbitmq:5672/
ENV CELERY_RESULT_BACKEND rpc://
ENV C_FORCE_ROOT true

# Copy requirements from add service and observability service
COPY services/add/requirements.txt /worker/services/add/requirements.txt
COPY observability/requirements.txt /worker/observability/requirements.txt

# Install necessary dependencies
RUN apt-get update --yes && \
    apt-get upgrade --yes && \
    apt-get install --yes --no-install-recommends \
    python3-dev \
    gcc && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies for the add service and observability service
RUN pip install --no-cache-dir -r /worker/services/add/requirements.txt
RUN pip install --no-cache-dir -r /worker/observability/requirements.txt

# Copy the application code for the add service and observability
COPY services/add /worker/services/add
COPY observability /worker/observability

# Set the OpenTelemetry endpoint
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317

# Specify the command to run Celery worker with OpenTelemetry instrumentation
CMD ["opentelemetry-instrument", "celery", "-A", "services.add.worker", "worker", "--loglevel=info", "-Q", "queue_add"]
