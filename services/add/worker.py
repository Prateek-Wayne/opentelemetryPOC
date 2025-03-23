import time
from celery import Celery
from observability.monitoring.monitoring import init_meter

# Initialize Celery client for the add service
celery_client = Celery('add', broker='pyamqp://rabbitmq')

# Initialize OpenTelemetry metrics
user_request_count, request_duration_histogram = init_meter("add_service")


@celery_client.task(name="add")
def add(x, y):
    start_time = time.time()
    
    # Perform the addition
    result = x + y
    
    # Measure the request duration
    duration_ms = (time.time() - start_time) * 1000
    
    # Record metrics
    user_request_count.add(1, {"task": "add", "status": "completed"})
    request_duration_histogram.record(duration_ms, {"task": "add", "status": "completed"})

    return result
