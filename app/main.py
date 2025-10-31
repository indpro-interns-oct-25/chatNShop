"""
Intent Classification API - Main Application Entry Point
"""
import sys
import os
import time  # <-- Import time for the retry logic
from contextlib import asynccontextmanager
from typing import Dict, Any
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List

# All imports should now work correctly, assuming
# all packages (like 'app', 'app/ai', etc.)
# have an '__init__.py' file.
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
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")  # NEW: support for Qdrant authentication
PRODUCT_COLLECTION_NAME = "chatnshop_products"
VECTOR_SIZE = 384  # This MUST match your embedding model (all-MiniLM-L6-v2)
# --- End Qdrant Configuration ---


# --- Initialize Qdrant Client with Retry Logic ---
print(f"Attempting to connect to Qdrant at {QDRANT_URL}...")
qdrant_client = None
retries = 5
wait_time = 3  # seconds

for i in range(retries):
    try:
        if QDRANT_API_KEY:  # Authenticated connection
            qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        else:  # Open access (legacy/no-auth)
            qdrant_client = QdrantClient(url=QDRANT_URL)
        # Try a basic health check to trigger connection (list_collections: harmless)
        qdrant_client.get_collections()
        print(f"✅ Connected to Qdrant at {QDRANT_URL}")
        break
    except Exception as e:
        print(f"Attempt {i + 1} failed: Could not connect to Qdrant. Is the Docker container running?")
        print(f"   Error detail: {e}")
        # Print any body/response if available (for HTTP errors)
        if hasattr(e, 'response') and getattr(e.response, 'content', None):
            print(f"Raw response content:\n{e.response.content}")
        if i < retries - 1:
            print(f"   Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        else:
            print("FAILED to initialize Qdrant client after 5 attempts.")

# --- End Qdrant Client Initialization ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    print(" Starting Intent Classification API...")
    
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
        print("⚠️ Queue infrastructure not available (will continue without async processing)")
    # --- End Queue Initialization ---
    
    # --- Initialize the Decision Engine singleton ---
    # This call will load all models on startup
    try:
        get_intent_classification("warm up")
        print(" Models loaded and Decision Engine is warm.")
    except Exception as e:
        print(f" ERROR during model warmup: {e}")

    # --- Initialize Qdrant Collection ---
    if qdrant_client:
        print(f"Checking for Qdrant collection '{PRODUCT_COLLECTION_NAME}'...")
        try:
            qdrant_client.create_collection(
                collection_name=PRODUCT_COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=VECTOR_SIZE,
                    distance=models.Distance.COSINE  # Cosine similarity is good for sentence embeddings
                )
            )
            print(f" Qdrant collection '{PRODUCT_COLLECTION_NAME}' created.")
        except Exception as e:
            # This is a common, expected error if the collection already exists
            if "already exists" in str(e).lower() or "exists" in str(e).lower():
                print(f" Qdrant collection '{PRODUCT_COLLECTION_NAME}' already exists.")
            else:
                # This would be an unexpected error (e.g., Qdrant server is down)
                print(f" ERROR: Could not create/verify Qdrant collection: {e}")
    else:
        print(" Qdrant client not initialized, skipping collection creation.")
    # --- End Qdrant Collection Initialization ---
        
    print(" Intent Classification API started successfully!")
    yield
    print("Shutting down Intent Classification API...")
    print(" Intent Classification API shut down successfully!")


# Create FastAPI application
app = FastAPI(
    title=os.getenv("APP_NAME", "Intent Classification API"),
    version=os.getenv("APP_VERSION", "1.0.0"),
    description="Hybrid rule-based + LLM intent classification backend for chatNShop",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=os.getenv("ALLOWED_METHODS", "GET,POST,PUT,DELETE").split(","),
    allow_headers=os.getenv("ALLOWED_HEADERS", "*").split(","),
)


@app.get("/", tags=["Health"])
async def root() -> Dict[str, Any]:
    """Root endpoint - API health check."""
    return {
        "status": "healthy",
        "service": "Intent Classification API",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "message": " Hybrid Intent Classification System is running!"
    }


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """Detailed health check endpoint."""
    from datetime import datetime
    
    # Check Qdrant connection status
    qdrant_status = "disconnected"
    if qdrant_client:
        try:
            qdrant_client.get_collections() # A simple health check operation
            qdrant_status = "connected"
        except Exception:
            qdrant_status = "unhealthy"
    
    # Check Redis/Queue status
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
    
    # Check OpenAI status (if configured)
    openai_status = "not_configured"
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            openai_status = "configured"
        else:
            openai_status = "not_configured"
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

# --- START OF CLASSIFICATION ENDPOINT ---

# 1. Define the input data model for classification
class ClassificationInput(BaseModel):
    text: str
    # You could add more fields here, like user_id, session_id, etc.


class ClassificationOutput(BaseModel):
    action_code: str = Field(..., description="Resolved action code")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence (0-1)")
    matched_keywords: List[str] = Field(default_factory=list, description="Matched keyword phrases")
    original_text: str = Field(..., description="Original input text")
    status: str = Field(..., description="Resolution status (e.g., CONFIDENT_KEYWORD, FALLBACK_*)")
    intent: Optional[Dict[str, Any]] = Field(default=None, description="Raw top intent payload for debug")

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
                        "action_code": "ADD_TO_CART",
                        "confidence_score": 0.92,
                        "matched_keywords": ["add to cart"],
                        "original_text": "Add this to my cart",
                        "status": "CONFIDENT_KEYWORD",
                        "intent": {
                            "id": "ADD_TO_CART",
                            "score": 0.92,
                            "source": "keyword",
                        },
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
    """
    Receives user text and returns the classified intent.
    
    This is the main endpoint for the intent classification service.
    """
    
    print(f"Received text for classification: {user_input.text}")
    
    try:
        # The classification function is synchronous (not async)
        result = get_intent_classification(user_input.text)

        # Normalize API output to include action_code, confidence_score, matched_keywords
        top = result.get("intent", {}) if isinstance(result, dict) else {}
        action_code = top.get("id") or top.get("intent")
        confidence_score = top.get("score")
        matched_kw = top.get("matched_text")
        if action_code is not None:
            result.setdefault("action_code", action_code)
        if confidence_score is not None:
            result.setdefault("confidence_score", confidence_score)
        if matched_kw:
            result.setdefault("matched_keywords", [matched_kw])

        # Add original text to the response
        result["original_text"] = user_input.text

        # --- TODO: Add Qdrant Search Logic ---
        # If the intent is "find_product" or similar,
        # you would now:
        # 1. Get the embedding for user_input.text (from your DecisionEngine or another service)
        # 2. Use qdrant_client.search(...) to find matching products
        # 3. Add the search results to the 'result' dictionary
        # --- End TODO ---
        
        # Shape to response model
        return ClassificationOutput(
            action_code=result.get("action_code", "UNKNOWN_INTENT"),
            confidence_score=float(result.get("confidence_score", 0.0)),
            matched_keywords=result.get("matched_keywords", []),
            original_text=user_input.text,
            status=str(result.get("status", "UNKNOWN")),
            intent=result.get("intent"),
        )

    except Exception as e:
        # Log the error for debugging
        print(f"ERROR: An error occurred in /classify: {e}")
        # Return a structured error response to the user
        return JSONResponse(
            status_code=500,
            content={
                "error": "Classification Failed",
                "message": "An internal error occurred while processing the request.",
                "detail": str(e)
            }
        )

# --- END OF CLASSIFICATION ENDPOINT ---


# Include API routers
app.include_router(intent_router)

# Include queue router if available
if QUEUE_ROUTER_AVAILABLE:
    try:
        app.include_router(queue_router, prefix="/api/v1")
    except Exception as e:
        print(f"⚠️ Failed to include queue router: {e}")

# app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["Feedback"])
# app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
# app.include_router(experiments.router, prefix="/api/v1/experiments", tags=["Experiments"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "path": str(request.url)
        }
    )


def run():
    """Run the application with uvicorn."""
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
