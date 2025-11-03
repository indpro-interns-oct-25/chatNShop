# app/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Summary, make_asgi_app
from prometheus_client import Info

# HTTP request metrics
REQUEST_COUNT = Counter(
    "chatnshop_http_requests_total",
    "Total HTTP requests processed",
    ["method", "endpoint", "http_status"]
)
REQUEST_IN_PROGRESS = Gauge(
    "chatnshop_inprogress_requests",
    "Number of in-progress HTTP requests"
)
REQUEST_LATENCY = Histogram(
    "chatnshop_request_latency_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"]
)

# App-level metrics
MODEL_CALL_COUNT = Counter(
    "chatnshop_model_calls_total",
    "Total number of model (LLM) calls",
    ["model"]
)
MODEL_CALL_LATENCY = Histogram(
    "chatnshop_model_call_latency_seconds",
    "Latency of model calls (seconds)",
    ["model"]
)
MODEL_CALL_ERRORS = Counter(
    "chatnshop_model_call_errors_total",
    "Number of errors from model calls",
    ["model", "error_type"]
)

# Confidence distribution: record a histogram by buckets
from prometheus_client import Histogram as PromHistogram
CONFIDENCE_HIST = PromHistogram(
    "chatnshop_prediction_confidence",
    "Distribution of confidence scores",
    buckets=(0.0, 0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0)
)

# Intent distribution
INTENT_COUNTER = Counter(
    "chatnshop_intent_distribution_total",
    "Count of predicted intents",
    ["intent"]
)

# Model cost (if you can compute tokens/cost per call)
MODEL_CALL_COST = Counter(
    "chatnshop_model_call_cost_cents_total",
    "Accumulated estimated model cost in cents",
    ["model"]
)

# Accuracy gauge updated by periodic job
ACCURACY_GAUGE = Gauge(
    "chatnshop_model_accuracy",
    "Rolling model accuracy (0-1)"
)

# Small app info metadata
APP_INFO = Info("chatnshop_app_info", "Application info")
APP_INFO.info({"version": "dev", "service": "chatnshop"})

# Helper to expose the ASGI metrics app
def get_metrics_asgi_app():
    return make_asgi_app()
