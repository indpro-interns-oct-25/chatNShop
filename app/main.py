"""
Intent Classification API - Main Application Entry Point
"""
import sys
import os
import time  # For Qdrant retry logic
from contextlib import asynccontextmanager
from typing import Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
from datetime import datetime

# Routers
from app.status_api import router as status_router
from app.api.cost_dashboard_api import router as cost_dashboard_router
from app.api.cost_dashboard_ui import router as cost_dashboard_ui_router
from app.ai.cost_monitor.scheduler import start_scheduler

# Decision Engine Import
print("Attempting to import Decision Engine...")
from app.ai.intent_classification.decision_engine import get_intent_classification
from app.api.v1.intent import router as intent_router
try:
    from app.api.v1.queue import router as queue_router
    QUEUE_ROUTER_AVAILABLE = True
except ImportError:
    QUEUE_ROUTER_AVAILABLE = False
print("Successfully imported Decision Engine.")

# --- Qdrant Client Import ---
from qdrant_client import QdrantClient, models
# --- End Qdrant Client Import ---

# Load environment variables
load_dotenv()

# --- Queue Infrastructure Import (CNS-21) ---
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
print(f"Attempting to connect to Qdrant at {QDRANT_URL}...")
qdrant_client = None
retries = 5
wait_time = 3  # seconds

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
        if i < retries - 1:
            print(f"   Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        else:
            print(f"❌ FAILED to initialize Qdrant client after {retries} attempts.")
# --- End Qdrant Client Initialization ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown manager."""
    print("🚀 Starting Intent Classification API...")

    # --- Initialize Queue Infrastructure (CNS-21) ---
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
    try:
        get_intent_classification("warm up")
        print("✅ Models loaded and Decision Engine is warm.")
    except Exception as e:
        print(f"❌ ERROR during model warmup: {e}")

    # --- Initialize Qdrant Collection ---
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
app = FastAPI(
    title=os.getenv("APP_NAME", "Intent Classification API"),
    version=os.getenv("APP_VERSION", "1.0.0"),
    description="Hybrid rule-based + LLM intent classification backend for chatNShop",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Health Endpoints ---
@app.get("/", tags=["Health"])
async def root() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "Intent Classification API",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "message": "Hybrid Intent Classification System is running!"
    }

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
            original_text=user_input.text,
            status=result.get("status", "UNKNOWN"),
            intent=result.get("intent"),
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

if __name__ == "__main__":
    run()
