import time
from fastapi import FastAPI
from celery.result import AsyncResult, GroupResult
from celery import group, signature
from worker import celery_client
from observability.monitoring.monitoring import init_meter
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from ..observability.monitoring.monitoring import init_meter
# from observability.monitoring.monitoring import init_meter  # Assuming monitoring.py has the init_meter function

app = FastAPI()


# ["opentelemetry-instrument", "--logs_exporter", "otlp", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# opentelemetry-instrument --logs_exporter otlp uvicorn api/api:app --host 0.0.0.0 --port 8000
# opentelemetry-instrument --logs_exporter otlp uvicorn api:app --host 0.0.0.0 --port 8000

# Initialize the meter and metrics when the app starts
user_request_count, request_duration_histogram = init_meter("fastapi_service")


@app.middleware("http")
async def add_metrics(request, call_next):
    # Increment the request counter
    user_request_count.add(1)

    # Start timing the request
    start_time = time.time()
    
    # Process the request
    response = await call_next(request)
    
    # Measure the request duration
    duration_ms = (time.time() - start_time) * 1000
    request_duration_histogram.record(duration_ms)

    return response


# ----------------------------
# Single task
# ----------------------------

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
        return {
            "task_id": task_id,
            "status": task_result.status,
            "result": task_result.get(),
        }
    else:
        return {
            "task_id": task_id,
            "status": task_result.status,
            "result": "Not ready",
        }


# ----------------------------
# Group task
# ----------------------------

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
