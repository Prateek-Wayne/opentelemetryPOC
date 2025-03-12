from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schema import UserCreate, UserUpdate
import time

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry import metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.semconv.resource import ResourceAttributes

# Define OpenTelemetry resources
resource = Resource.create({ResourceAttributes.SERVICE_NAME: "prateek_CRUD_app"})

# Configure OTLP Exporter
exporter = OTLPMetricExporter(endpoint="http://otel-collector:4317", insecure=True)
reader = PeriodicExportingMetricReader(exporter, export_interval_millis=10000)

# Set up MeterProvider
meterProvider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(meterProvider)
meter = metrics.get_meter(__name__)

# 1️⃣ User request counter
user_request_count = meter.create_counter(
    name="prateek_app_user_request_count",
    description="Counts the requests to user-service",
    unit="1"
)

# 2️⃣ User creation counter
user_created_count = meter.create_counter(
    name="prateek_app_user_created_count",
    description="Counts the number of users created",
    unit="1"
)

# 3️⃣ User update counter
user_updated_count = meter.create_counter(
    name="prateek_app_user_updated_count",
    description="Counts the number of user update requests",
    unit="1"
)

# 4️⃣ User deletion counter
user_deleted_count = meter.create_counter(
    name="prateek_app_user_deleted_count",
    description="Counts the number of users deleted",
    unit="1"
)

# 5️⃣ Active user gauge
active_users_gauge = meter.create_up_down_counter(
    name="prateek_app_active_users",
    description="Tracks the number of active users in the system",
    unit="1"
)

# 6️⃣ Request duration histogram
request_duration_histogram = meter.create_histogram(
    name="prateek_app_request_duration",
    description="Measures the duration of requests",
    unit="ms"
)

app = FastAPI()

@app.get("/users/")
def get_all_users(db: Session = Depends(get_db)):
    start_time = time.time()

    user_request_count.add(1)
    users = db.query(User).all()

    request_duration_histogram.record((time.time() - start_time) * 1000)  # Convert to milliseconds
    return users

@app.get("/users/{user_id}")
def get_user_by_email(user_id: int, db: Session = Depends(get_db)):
    start_time = time.time()

    user = db.query(User).filter(User.id == user_id).first()
    request_duration_histogram.record((time.time() - start_time) * 1000)  # Convert to milliseconds

    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    start_time = time.time()

    db_user = User(name=user.name, email=user.email, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    user_created_count.add(1)
    active_users_gauge.add(1)
    request_duration_histogram.record((time.time() - start_time) * 1000)  # Convert to milliseconds

    return db_user

@app.put("/users/{user_id}")
def update_user_by_email(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    start_time = time.time()

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.name = user.name
    db_user.email = user.email
    db.commit()

    user_updated_count.add(1)
    request_duration_histogram.record((time.time() - start_time) * 1000)  # Convert to milliseconds

    return {"message": "User updated successfully"}

@app.delete("/users/{user_id}")
def delete_user_by_email(user_id: int, db: Session = Depends(get_db)):
    start_time = time.time()

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(db_user)
    db.commit()

    user_deleted_count.add(1)
    active_users_gauge.add(-1)  # Decrease active user count
    request_duration_histogram.record((time.time() - start_time) * 1000)  # Convert to milliseconds

    return {"message": "User deleted successfully"}
