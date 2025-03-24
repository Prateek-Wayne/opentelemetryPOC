import time
from fastapi import FastAPI
from celery.result import AsyncResult, GroupResult
from celery import group, signature
from worker import celery_client
from observability.monitoring.monitoring import init_meter
from opentelemetry.trace import Status, StatusCode
from observability.tracing.tracing import init_tracer
import threading
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI()

user_request_count, request_duration_histogram = init_meter("fastapi_service")

@app.middleware("http")
async def add_metrics(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    request_path = request.url.path
    status_code = response.status_code
    request_method = request.method
    user_request_count.add(1, {"route": request_path, "status_code": status_code, "method": request_method})
    request_duration_histogram.record(duration_ms, {"route": request_path, "status_code": status_code, "method": request_method})
    return response

tracer = init_tracer("fastapi_service")
user_request_count, request_duration_histogram = init_meter("fastapi_service")

@app.middleware("http")
async def add_tracing(request, call_next):
    with tracer.start_as_current_span("http_request") as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        span.set_attribute("http.status_code", response.status_code)
        if response.status_code >= 400:
            span.set_status(Status(StatusCode.ERROR))
        user_request_count.add(1, {"route": request.url.path, "status_code": response.status_code})
        request_duration_histogram.record(duration_ms, {"route": request.url.path, "status_code": response.status_code})
        return response

@app.post("/add")
async def add_task(x: int, y: int):
    task = celery_client.send_task("add", args=[x, y], queue="queue_add")
    return {"task_id": task.id}

@app.post("/multiply")
async def multiply_task(x: int, y: int):
    task = celery_client.send_task("multiply", args=[x, y], queue="queue_multiply")
    return {"task_id": task.id}

@app.get("/check/{task_id}")
async def get_task_result(task_id: str):
    task_result = AsyncResult(task_id, app=celery_client)
    if task_result.ready():
        return {"task_id": task_id, "status": task_result.status, "result": task_result.get()}
    else:
        return {"task_id": task_id, "status": task_result.status, "result": "Not ready"}

@app.post("/multiply_and_add")
async def multiply_and_add_task(x: int, y: int):
    group_task = group(
        signature("multiply", args=[x, y], queue="queue_multiply"),
        signature("add", args=[x, y], queue="queue_add"),
    )()
    group_task.save()
    return {"group_task_id": group_task.id}

@app.get("/check_group/{group_task_id}")
async def get_group_task_result(group_task_id: str):
    task_result = GroupResult.restore(group_task_id, app=celery_client)
    if task_result.ready():
        return {
            "group_task_id": group_task_id,
            "status": [task.status for task in task_result],
            "result": task_result.get(),
        }
    else:
        return {
            "group_task_id": group_task_id,
            "status": [task.status for task in task_result],
            "result": "Not ready",
        }

# New Endpoint to Create CPU Spikes
def cpu_spike():
    end_time = time.time() + 10  # Run the CPU spike for 10 seconds
    while time.time() < end_time:
        # Perform a CPU-intensive task
        sum([i * i for i in range(100000)])

@app.get("/cpu_spike")
async def create_cpu_spike():
    threading.Thread(target=cpu_spike).start()  # Run CPU spike in a separate thread
    return {"message": "CPU spike started!"}
