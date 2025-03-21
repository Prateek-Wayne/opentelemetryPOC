import time
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
import os

# Initialize the meter and metrics
def init_meter(service_name: str):
    resource = Resource.create({SERVICE_NAME: service_name})
    otlp_exporter = OTLPMetricExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317"))
    metric_reader = PeriodicExportingMetricReader(otlp_exporter)
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    meter = meter_provider.get_meter(__name__)
    
    # Create metrics (counters, histograms, etc.)
    user_request_count = meter.create_counter(
        name="api_request_count",
        description="Counts the requests to user-service",
        unit="1"
    )

    request_duration_histogram = meter.create_histogram(
        name="api_request_count",
        description="Measures the duration of requests",
        unit="ms"
    )

    return user_request_count, request_duration_histogram
