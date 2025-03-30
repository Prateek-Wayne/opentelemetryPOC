import time
from celery import Celery
from observability.monitoring.monitoring import init_meter

# Initialize Celery client for the add service
celery_client = Celery('add', broker='pyamqp://rabbitmq')

# Initialize OpenTelemetry metrics
http_requests_total, http_request_duration = init_meter("add_service")


@celery_client.task(name="add")
def add(x, y):
    start_time = time.time()
    
    # Perform the addition
    result = x + y
    
    # Measure the request duration
    duration_ms = (time.time() - start_time) * 1000
    
    # Record metrics
    http_requests_total.add(1, {"task": "add", "status": "completed"})
    http_request_duration.record(duration_ms, {"task": "add", "status": "completed"})

    return result
