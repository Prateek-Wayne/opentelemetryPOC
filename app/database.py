from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import time

# OpenTelemetry Imports
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.semconv.resource import ResourceAttributes

# Database Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, '../users.db')}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# OpenTelemetry Setup
resource = Resource.create({ResourceAttributes.SERVICE_NAME: "prateek_CRUD_app"})

exporter = OTLPMetricExporter(endpoint="http://otel-collector:4317", insecure=True)
reader = PeriodicExportingMetricReader(exporter, export_interval_millis=10000)

meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(__name__)

# Define Metrics
db_query_count = meter.create_counter(
    name="prateek_db_query_count",
    description="Counts the number of database queries executed",
    unit="1"
)

db_query_duration = meter.create_histogram(
    name="prateek_db_query_duration",
    description="Measures the execution time of database queries",
    unit="ms"
)

# Dependency Injection for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield instrumented_db_session(db)
    finally:
        db.close()

# Instrumented DB Session
class instrumented_db_session:
    def __init__(self, db):
        self.db = db

    def execute(self, *args, **kwargs):
        start_time = time.time()
        result = self.db.execute(*args, **kwargs)
        duration = (time.time() - start_time) * 1000  # Convert to milliseconds

        db_query_count.add(1)
        db_query_duration.record(duration)

        return result

    def __getattr__(self, name):
        return getattr(self.db, name)
