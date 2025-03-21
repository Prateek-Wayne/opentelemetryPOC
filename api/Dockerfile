FROM python:3.11.3-slim
WORKDIR /home

ENV CELERY_BROKER_URL pyamqp://guest:guest@localhost:5672/
ENV CELERY_RESULT_BACKEND rpc://
ENV C_FORCE_ROOT true

# Set the host and port for Uvicorn
ENV HOST 0.0.0.0
ENV PORT 8000
ENV DEBUG True

# Copy requirements from api and observability
COPY /api/requirements.txt /home/api/requirements.txt
COPY /observability/requirements.txt /home/observability/requirements.txt

# Install necessary dependencies
RUN apt-get update --yes && \
    apt-get upgrade --yes && \
    apt-get install --yes --no-install-recommends \
    python3-dev \
    gcc && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the application code
COPY /api /home/api
COPY /observability /home/observability

# Install Python dependencies for both the api and observability
RUN pip install -r /home/api/requirements.txt
RUN pip install -r /home/observability/requirements.txt

# Install OpenTelemetry auto-instrumentation
RUN opentelemetry-bootstrap -a install

# Expose the API port
EXPOSE ${PORT}

# Set the OpenTelemetry endpoint
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317

# Use the correct working directory when launching Uvicorn
WORKDIR /home/api

# Start the API with OpenTelemetry instrumentation
CMD opentelemetry-instrument --logs_exporter otlp uvicorn api:app --host ${HOST} --port ${PORT}
# CMD /bin/sh -c "foreman start -f myprocfile || sleep 2073600"
