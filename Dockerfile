FROM python:3.11.3-slim

WORKDIR /home

# Install all OS dependencies for fully functional requirements.txt install
RUN apt-get update --yes && \
    apt-get upgrade --yes && \
    apt-get install --yes --no-install-recommends \
    # - apt-get upgrade is run to patch known vulnerabilities in apt-get packages as
    #   the python base image may be rebuilt too seldom sometimes (less than once a month)
    # required for psutil python package to install
    python3-dev \
    gcc && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt .

RUN pip install -r requirements.txt
RUN opentelemetry-bootstrap -a install



COPY . .  

EXPOSE 8000

ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317

CMD ["opentelemetry-instrument", "--logs_exporter", "otlp", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
