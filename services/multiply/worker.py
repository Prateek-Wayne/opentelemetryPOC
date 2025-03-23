import time
import os
from celery import Celery
from observability.monitoring.monitoring import init_meter  # Import the monitoring module

# Set up Celery broker and result backend
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis")
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "pyamqp://guest:guest@rabbitmq:5672/")

# Initialize Celery client for the multiply service
celery = Celery(
    __name__,
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

celery.conf.task_routes = {
    "worker.*": {"queue": "queue_multiply"},
}

# Initialize OpenTelemetry metrics
user_request_count, request_duration_histogram = init_meter("multiply_service")


@celery.task(name="multiply")
def multiply(x, y):
    start_time = time.time()  # Start time for measuring duration
    
    # Perform the multiplication
    result = x * y
    
    # Measure the request duration
    duration_ms = (time.time() - start_time) * 1000
    
    # Record metrics
    user_request_count.add(1, {"task": "multiply", "status": "completed"})
    request_duration_histogram.record(duration_ms, {"task": "multiply", "status": "completed"})
    
    return result
