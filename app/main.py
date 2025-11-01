"""
Intent Classification API - Main Application Entry Point
"""
import sys
import os
import time  # For Qdrant retry logic
import time
import uuid
import traceback
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
from datetime import datetime

# Routers
from app.status_api import router as status_router
from app.api.cost_dashboard_api import router as cost_dashboard_router
from app.api.cost_dashboard_ui import router as cost_dashboard_ui_router
from app.ai.cost_monitor.scheduler import start_scheduler

# Decision Engine Import
import uvicorn

# ✅ Structured logging with correlation ID and error context
def log_with_context(level: str, message: str, error: Exception | None = None, context: Optional[str] = None):
    correlation_id = str(uuid.uuid4())
    base_log = f"[{level}] [{correlation_id}] {message}"
    if error:
        stack = traceback.format_exc()
        print(f"{base_log}\nError: {error}\nStack Trace:\n{stack}")
    else:
        print(base_log)
    return correlation_id


# ✅ Import resilient OpenAI client
try:
    from app.core.resilient_openai_client import resilient_client
except Exception:
    resilient_client = None

# ✅ Import decision engine and routers
print("Attempting to import Decision Engine...")
from app.ai.intent_classification.decision_engine import get_intent_classification
from app.api.v1.intent import router as intent_router
try:
    from app.api.v1.queue import router as queue_router
    QUEUE_ROUTER_AVAILABLE = True
except ImportError:
    QUEUE_ROUTER_AVAILABLE = False
try:
    from app.api.v1.cache import router as cache_router
    CACHE_ROUTER_AVAILABLE = True
except ImportError:
    CACHE_ROUTER_AVAILABLE = False
print("Successfully imported Decision Engine.")

# ✅ Qdrant client setup
from qdrant_client import QdrantClient, models

# ✅ Load environment variables
load_dotenv()

# --- Queue Infrastructure Import (CNS-21) ---
# ✅ Queue Infrastructure Import (CNS-21)
# --- Queue Infrastructure Import ---
try:
    from app.queue.queue_manager import queue_manager
    from app.queue.monitor import queue_monitor
    QUEUE_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Queue infrastructure not available: {e}")
    queue_manager = None
    queue_monitor = None
    QUEUE_AVAILABLE = False
# --- End Queue Infrastructure Import ---

# --- Qdrant Configuration ---
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")  # optional auth
PRODUCT_COLLECTION_NAME = "chatnshop_products"
VECTOR_SIZE = 384  # Must match embedding model
# --- End Qdrant Configuration ---

# --- Initialize Qdrant Client with Retry Logic ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
# Use QDRANT_URL if set, otherwise construct from host/port

# ✅ Qdrant Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
PRODUCT_COLLECTION_NAME = "chatnshop_products"
VECTOR_SIZE = 384  # must match embedding model
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

if not QDRANT_URL or QDRANT_URL == "http://localhost:6333":
    QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_PORT}"

print(f"Attempting to connect to Qdrant at {QDRANT_URL}...")
qdrant_client = None
retries = 5
wait_time = 3

for i in range(retries):
    try:
        client = QdrantClient(QDRANT_URL, timeout=10)
        client.get_collections()
        qdrant_client = client
        if QDRANT_API_KEY:
            qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        else:
            qdrant_client = QdrantClient(url=QDRANT_URL)
        qdrant_client.get_collections()
        print(f"✅ Connected to Qdrant at {QDRANT_URL}")
        break
    except Exception as e:
        print(f"Attempt {i + 1} failed: Could not connect to Qdrant.")
        print(f"   Error detail: {e}")
        print(f"Attempt {i + 1} failed: Could not connect to Qdrant. Error: {e}")
        if i < retries - 1:
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        else:
            print(f"❌ FAILED to initialize Qdrant client after {retries} attempts.")
# --- End Qdrant Client Initialization ---
            print("❌ FAILED to initialize Qdrant client after 5 attempts.")


# ✅ Lifespan hook (app startup/shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown manager."""
    print("🚀 Starting Intent Classification API...")

    # --- Initialize Queue Infrastructure (CNS-21) ---
    print("🚀 Starting Intent Classification API...")

    # Queue initialization
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    print(" Starting Intent Classification API...")
    
    # --- Initialize Queue Infrastructure ---
    if QUEUE_AVAILABLE and queue_manager:
        try:
            if queue_manager.health_check():
                print("✅ Queue infrastructure ready (Redis connected)")
            else:
                print("⚠️ Queue infrastructure available but Redis not connected")
        except Exception as e:
            print(f"⚠️ Queue health check failed: {e}")
    else:
        print("⚠️ Queue infrastructure not available (continuing without async processing)")

    # --- Model Warmup ---
    # Warm up Decision Engine (load models)
    try:
        get_intent_classification("warm up")
        print("✅ Models loaded and Decision Engine is warm.")
    except Exception as e:
        print(f"❌ ERROR during model warmup: {e}")
        log_with_context("ERROR", "Model warmup failed", e)

    # Verify or create Qdrant collection
    if qdrant_client:
        try:
            qdrant_client.create_collection(
                collection_name=PRODUCT_COLLECTION_NAME,
                vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE)
            )
            print(f"✅ Qdrant collection '{PRODUCT_COLLECTION_NAME}' created.")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"ℹ️ Qdrant collection '{PRODUCT_COLLECTION_NAME}' already exists.")
            else:
                print(f"❌ Could not create/verify Qdrant collection: {e}")
    else:
        print("⚠️ Qdrant client not initialized, skipping collection creation.")

    # --- Initialize Cost Monitoring Scheduler ---
    try:
        start_scheduler()
        print("✅ Cost monitoring scheduler initialized.")
    except Exception as e:
        print(f"⚠️ Scheduler init failed: {e}")

    yield
    print("🛑 Shutting down Intent Classification API...")
    print("✅ Shutdown complete.")


# --- FastAPI App Initialization ---
                log_with_context("ERROR", "Could not create/verify Qdrant collection", e)
    else:
        print("⚠️ Qdrant client not initialized, skipping collection creation.")

    print("✅ Intent Classification API started successfully!")
    yield
    print("🛑 Shutting down Intent Classification API...")
    print("✅ Intent Classification API shut down successfully!")


# ✅ FastAPI app setup
app = FastAPI(
    title=os.getenv("APP_NAME", "Intent Classification API"),
    version=os.getenv("APP_VERSION", "1.0.0"),
    description="Hybrid rule-based + LLM intent classification backend for chatNShop",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# --- CORS ---
# ✅ Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Health Endpoints ---

# ✅ Root Endpoint
@app.get("/", tags=["Health"])
async def root() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "Intent Classification API",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "message": "Hybrid Intent Classification System is running!"
    }


# ✅ Health Endpoint
@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    qdrant_status = "disconnected"
    if qdrant_client:
        try:
            qdrant_client.get_collections()
            qdrant_status = "connected"
        except Exception:
            qdrant_status = "unhealthy"

    redis_status = "unavailable"
    queue_stats = {}
    if QUEUE_AVAILABLE and queue_manager:
        try:
            if queue_manager.health_check():
                redis_status = "connected"
                queue_stats = queue_manager.get_queue_stats()
            else:
                redis_status = "disconnected"
        except Exception as e:
            redis_status = f"error: {str(e)}"

    openai_status = "configured" if os.getenv("OPENAI_API_KEY") else "not_configured"
    overall_status = "healthy" if qdrant_status == "connected" and "connected" in redis_status else "degraded"
    openai_status = "not_configured"
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        openai_status = "configured" if api_key else "not_configured"
    except Exception:
        openai_status = "unknown"

    overall_status = "healthy"
    if qdrant_status == "unhealthy" or redis_status.startswith("error"):
        overall_status = "degraded"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "services": {
            "qdrant": qdrant_status,
            "redis": redis_status,
            "openai": openai_status
        },
        "queue": queue_stats,
        "version": os.getenv("APP_VERSION", "1.0.0")
    }

# --- Intent Classification Endpoint ---
class ClassificationInput(BaseModel):
    text: str

class ClassificationOutput(BaseModel):
    action_code: str
    confidence_score: float
    matched_keywords: List[str]
    original_text: str
    status: str
    intent: Optional[Dict[str, Any]] = None

@app.post("/classify", tags=["Intent Classification"], response_model=ClassificationOutput)
async def classify_intent(user_input: ClassificationInput) -> ClassificationOutput:
    try:
        result = get_intent_classification(user_input.text)
        top = result.get("intent", {}) if isinstance(result, dict) else {}
        result["original_text"] = user_input.text
        return ClassificationOutput(
            action_code=top.get("id", "UNKNOWN_INTENT"),
            confidence_score=float(top.get("score", 0.0)),
            matched_keywords=[top.get("matched_text")] if top.get("matched_text") else [],

# ✅ Classification Endpoint
class ClassificationInput(BaseModel):
    text: str


class ClassificationOutput(BaseModel):
    action_code: str = Field(..., description="Resolved action code")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    matched_keywords: List[str] = Field(default_factory=list)
    original_text: str = Field(...)
    status: str = Field(...)
    intent: Optional[Dict[str, Any]] = Field(default=None)


@app.post("/classify", tags=["Intent Classification"], response_model=ClassificationOutput)
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence (0-1)")
    matched_keywords: List[str] = Field(default_factory=list, description="Matched keyword phrases")
    original_text: str = Field(..., description="Original input text")
    status: str = Field(..., description="Resolution status (e.g., CONFIDENT_KEYWORD, FALLBACK_*)")
    intent: Optional[Dict[str, Any]] = Field(default=None, description="Raw top intent payload for debug")
    entities: Optional[Dict[str, Any]] = Field(default=None, description="Extracted entities (product, brand, color, etc.)")

# 2. Create the classification POST endpoint
@app.post(
    "/classify",
    tags=["Intent Classification"],
    response_model=ClassificationOutput,
    summary="Classify user input into an intent",
    responses={
        200: {
            "description": "Classification result",
            "content": {
                "application/json": {
                    "example": {
                        "action_code": "SEARCH_PRODUCT",
                        "confidence_score": 0.92,
                        "matched_keywords": ["search", "shoes"],
                        "original_text": "Show me red Nike running shoes under $100",
                        "status": "LLM_CLASSIFICATION",
                        "intent": {
                            "id": "SEARCH_PRODUCT",
                            "score": 0.92,
                            "source": "llm",
                        },
                        "entities": {
                            "product_type": "shoes",
                            "category": "running",
                            "brand": "Nike",
                            "color": "red",
                            "size": null,
                            "price_range": {"min": null, "max": 100, "currency": "USD"}
                        }
                    }
                }
            },
        },
        500: {
            "description": "Internal error",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Classification Failed",
                        "message": "An internal error occurred while processing the request.",
                        "detail": "<error details>",
                    }
                }
            },
        },
    },
)
async def classify_intent(user_input: ClassificationInput) -> ClassificationOutput:
    correlation_id = str(uuid.uuid4())
    print(f"[INFO] [{correlation_id}] Received text: {user_input.text}")

    try:
        result = get_intent_classification(user_input.text)
        top = result.get("intent", {}) if isinstance(result, dict) else {}
        action_code = top.get("id") or top.get("intent")
        confidence_score = top.get("score")
        matched_kw = top.get("matched_text")

        result.setdefault("action_code", action_code or "UNKNOWN_INTENT")
        result.setdefault("confidence_score", confidence_score or 0.0)
        if matched_kw:
            result.setdefault("matched_keywords", [matched_kw])
        result["original_text"] = user_input.text

        return ClassificationOutput(
            action_code=result["action_code"],
            confidence_score=float(result["confidence_score"]),
            matched_keywords=result.get("matched_keywords", []),
            original_text=user_input.text,
            status=result.get("status", "UNKNOWN"),
            intent=result.get("intent"),
            entities=result.get("entities"),  # NEW: Include entities in response
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Classification Failed", "detail": str(e)})

# --- Include Routers ---
app.include_router(intent_router)
app.include_router(status_router)
app.include_router(cost_dashboard_router)
app.include_router(cost_dashboard_ui_router)

if QUEUE_ROUTER_AVAILABLE:
    app.include_router(queue_router, prefix="/api/v1")

# --- Exception Handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "Internal server error", "path": str(request.url)})

# --- Run Server ---
def run():
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
        error_id = log_with_context("ERROR", "Classification failed", e, context=user_input.text)
        if resilient_client:
            fallback = resilient_client.call(user_input.text)
            print(f"[WARN] [{error_id}] Using resilient fallback: {fallback}")
            return ClassificationOutput(
                action_code=fallback.get("action_code", "UNKNOWN_INTENT"),
                confidence_score=float(fallback.get("confidence", 0.0)),
                matched_keywords=[],
                original_text=user_input.text,
                status="FALLBACK_LLM",
                intent=fallback,
            )
        return JSONResponse(
            status_code=500,
            content={
                "error": "Classification Failed",
                "message": "Internal processing error. Please retry.",
                "error_id": error_id,
            },
        )


# ✅ Include routers
app.include_router(intent_router)
if QUEUE_ROUTER_AVAILABLE:
    try:
        app.include_router(queue_router, prefix="/api/v1")
    except Exception as e:
        print(f"⚠️ Failed to include queue router: {e}")

# Include cache router if available
if CACHE_ROUTER_AVAILABLE:
    try:
        app.include_router(cache_router, prefix="/api/v1")
    except Exception as e:
        print(f"⚠️ Failed to include cache router: {e}")

# app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["Feedback"])
# app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
# app.include_router(experiments.router, prefix="/api/v1/experiments", tags=["Experiments"])

# ✅ Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_id = log_with_context("ERROR", f"Unhandled exception at {request.url}", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "error_id": error_id,
            "path": str(request.url),
        },
    )


# ✅ Entrypoint
def run():
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 8000)),
        reload=False,
        workers=int(os.getenv("WORKERS", 1)),
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )


if __name__ == "__main__":
    run()
