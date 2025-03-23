FROM python:3.11.3-slim
WORKDIR /worker

ENV CELERY_BROKER_URL pyamqp://guest:guest@localhost:5672/
ENV CELERY_RESULT_BACKEND rpc://
ENV C_FORCE_ROOT true

COPY services/multiply/requirements.txt /worker/services/multiply/requirements.txt
COPY observability/requirements.txt /worker/observability/requirements.txt

RUN apt-get update --yes && \
    apt-get upgrade --yes && \
    apt-get install --yes --no-install-recommends \
    python3-dev \
    gcc && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r /worker/services/multiply/requirements.txt
RUN pip install --no-cache-dir -r /worker/observability/requirements.txt


COPY services/multiply /worker/services/multiply
COPY observability /worker/observability
RUN opentelemetry-bootstrap -a install

# ENV OTFROM python:3.11.3-slimEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317



# Specify the command to run on container start
CMD ["opentelemetry-instrument", "celery", "-A", "services.multiply.worker", "worker", "--loglevel=info", "-Q", "queue_multiply"]