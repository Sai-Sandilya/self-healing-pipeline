from prometheus_client import Counter, Gauge, Histogram, start_http_server
import threading
import time
from typing import Optional

class MetricsManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MetricsManager, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        
        # Define Metrics
        self.pipeline_runs = Counter(
            'shp_pipeline_runs_total', 
            'Total number of pipeline runs',
            ['status'] # success, failure
        )
        
        self.pipeline_errors = Counter(
            'shp_pipeline_errors_total',
            'Total number of pipeline errors',
            ['type'] # schema_drift, type_mismatch, etc.
        )
        
        self.healing_attempts = Counter(
            'shp_healing_attempts_total',
            'Total number of healing attempts',
            ['status'] # success, failure
        )
        
        self.pipeline_duration = Histogram(
            'shp_pipeline_duration_seconds',
            'Time spent running the pipeline',
            buckets=[1, 5, 10, 30, 60, 120, 300]
        )
        
        self.ai_cost = Counter(
            'shp_ai_cost_total',
            'Estimated cost of AI calls in USD'
        )
        
        self.last_run_timestamp = Gauge(
            'shp_last_run_timestamp_seconds',
            'Timestamp of the last pipeline run'
        )

        # Start Prometheus HTTP Server
        try:
            start_http_server(8000)
            print("✓ Metrics server started on port 8000")
        except OSError:
            print("⚠ Metrics server port 8000 likely already in use. Skipping start.")

    def record_pipeline_run(self, status: str, duration: float):
        self.pipeline_runs.labels(status=status).inc()
        self.pipeline_duration.observe(duration)
        self.last_run_timestamp.set(time.time())

    def record_error(self, error_type: str):
        self.pipeline_errors.labels(type=error_type).inc()

    def record_healing(self, status: str):
        self.healing_attempts.labels(status=status).inc()

    def record_cost(self, amount: float):
        self.ai_cost.inc(amount)
