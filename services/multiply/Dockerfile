FROM python:3.11.3-slim

ENV CELERY_BROKER_URL pyamqp://guest:guest@localhost:5672/
ENV CELERY_RESULT_BACKEND rpc://
ENV C_FORCE_ROOT true

COPY requirements.txt /tmp/requirements.txt
RUN apt-get update --yes && \
    apt-get upgrade --yes && \
    apt-get install --yes --no-install-recommends \
    # - apt-get upgrade is run to patch known vulnerabilities in apt-get packages as
    #   the python base image may be rebuilt too seldom sometimes (less than once a month)
    # required for psutil python package to install
    python3-dev \
    gcc && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
# RUN pip install -U setuptools pip
RUN pip install --no-cache-dir -r /tmp/requirements.txt
# RUN opentelemetry-bootstrap -a install

# ENV OTFROM python:3.11.3-slimEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317


WORKDIR /worker


# Specify the command to run on container start
CMD ["celery", "-A", "multiply", "worker", "--loglevel=info", "-Q", "queue_multiply"]