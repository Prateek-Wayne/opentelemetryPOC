from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schema import UserCreate, UserUpdate
import time
import logging

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry import metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.semconv.resource import ResourceAttributes

from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
# from opentelemetry.sdk._logs import SeverityWithTextProcessor  # Added import for severity processor

# Define OpenTelemetry resources
resource = Resource.create({ResourceAttributes.SERVICE_NAME: "prateek_CRUD_app"})

# Configure OTLP Exporter for metrics
exporter = OTLPMetricExporter(endpoint="http://otel-collector:4317", insecure=True)
reader = PeriodicExportingMetricReader(exporter, export_interval_millis=10000)

# Set up MeterProvider for metrics
meterProvider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(meterProvider)
meter = metrics.get_meter(__name__)

# Configure OTLP Exporter for logs
log_exporter = OTLPLogExporter(endpoint="http://otel-collector:4317", insecure=True)
log_processor = BatchLogRecordProcessor(log_exporter)

# Updated logger provider configuration with SeverityWithTextProcessor
logger_provider = LoggerProvider(
    resource=resource  # This processor maps Python log levels to OpenTelemetry severity
)
logger_provider.add_log_record_processor(log_processor)
set_logger_provider(logger_provider)

# Use logging.ERROR as the minimum level to capture
handler = LoggingHandler( logger_provider=logger_provider)

# Set up logging - ensure proper propagation of log levels
logging.basicConfig(level=logging.NOTSET, handlers=[handler])
logger = logging.getLogger("prateek_CRUD_logger")

# Metrics
user_request_count = meter.create_counter(
    name="prateek_app_user_request_count",
    description="Counts the requests to user-service",
    unit="1"
)

user_created_count = meter.create_counter(
    name="prateek_app_user_created_count",
    description="Counts the number of users created",
    unit="1"
)

user_updated_count = meter.create_counter(
    name="prateek_app_user_updated_count",
    description="Counts the number of user update requests",
    unit="1"
)

user_deleted_count = meter.create_counter(
    name="prateek_app_user_deleted_count",
    description="Counts the number of users deleted",
    unit="1"
)

active_users_gauge = meter.create_up_down_counter(
    name="prateek_app_active_users",
    description="Tracks the number of active users in the system",
    unit="1"
)

request_duration_histogram = meter.create_histogram(
    name="prateek_app_request_duration",
    description="Measures the duration of requests",
    unit="ms"
)

app = FastAPI()

@app.get("/users/")
def get_all_users(db: Session = Depends(get_db)):
    start_time = time.time()
    logger.info("Fetching all users.")

    user_request_count.add(1)
    users = db.query(User).all()

    duration = (time.time() - start_time) * 1000  # Convert to milliseconds
    request_duration_histogram.record(duration)
    logger.info(f"Fetched all users successfully. Duration: {duration} ms")
    
    return users

@app.get("/users/{user_id}")
def get_user_by_email(user_id: int, db: Session = Depends(get_db)):
    start_time = time.time()
    logger.info(f"Fetching user with ID: {user_id}.")

    user = db.query(User).filter(User.id == user_id).first()
    duration = (time.time() - start_time) * 1000  # Convert to milliseconds
    request_duration_histogram.record(duration)

    if user:
        logger.info(f"User {user_id} found. Duration: {duration} ms")
        return user
    
    logger.error(f"User {user_id} not found. Duration: {duration} ms")
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    start_time = time.time()
    logger.info("Creating new user.")

    # Check if user with the same email already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        logger.error(f"User with email {user.email} already exists.")
        raise HTTPException(status_code=400, detail="User with this email already exists")

    db_user = User(name=user.name, email=user.email, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    user_created_count.add(1)
    active_users_gauge.add(1)
    duration = (time.time() - start_time) * 1000  # Convert to milliseconds
    request_duration_histogram.record(duration)

    logger.info(f"User created successfully. Duration: {duration} ms")
    return db_user

@app.put("/users/{user_id}")
def update_user_by_email(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    start_time = time.time()
    logger.info(f"Updating user with ID: {user_id}.")

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        logger.error(f"User {user_id} not found for update.")
        raise HTTPException(status_code=404, detail="User not found")

    db_user.name = user.name
    db_user.email = user.email
    db.commit()

    user_updated_count.add(1)
    duration = (time.time() - start_time) * 1000  # Convert to milliseconds
    request_duration_histogram.record(duration)

    logger.info(f"User {user_id} updated successfully. Duration: {duration} ms")
    return {"message": "User updated successfully"}

@app.delete("/users/{user_id}")
def delete_user_by_email(user_id: int, db: Session = Depends(get_db)):
    start_time = time.time()
    logger.info(f"Deleting user with ID: {user_id}.")

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        logger.error(f"User {user_id} not found for deletion.")
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(db_user)
    db.commit()

    user_deleted_count.add(1)
    active_users_gauge.add(-1)
    duration = (time.time() - start_time) * 1000  # Convert to milliseconds
    request_duration_histogram.record(duration)

    logger.info(f"User {user_id} deleted successfully. Duration: {duration} ms")
    return {"message": "User deleted successfully"}