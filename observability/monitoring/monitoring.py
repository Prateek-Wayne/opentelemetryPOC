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
        name="prateek_app_user_request_count",
        description="Counts the requests to user-service",
        unit="1"
    )

    request_duration_histogram = meter.create_histogram(
        name="prateek_app_request_duration",
        description="Measures the duration of requests",
        unit="ms"
    )

    return user_request_count, request_duration_histogram

# Record request count and duration
# def handle_request():
#     # Increment the request counter
#     user_request_count.add(1)
    
#     # Record the request duration
#     start_time = time.time()  # Start time of the request
#     # Simulate the operation (e.g., handling a request)
#     time.sleep(0.5)  # Simulating a request operation that takes 0.5 seconds
#     end_time = time.time()  # End time of the request
    
#     # Calculate the duration in milliseconds and record it in the histogram
#     duration_ms = (end_time - start_time) * 1000
#     request_duration_histogram.record(duration_ms)

if __name__ == "__main__":
    # Initialize the meter and metrics
    user_request_count, request_duration_histogram = init_meter("user_service")
    
    # Simulate a request being handled
    # handle_request()
