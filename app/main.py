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
from pydantic import BaseModel

# All imports should now work correctly, assuming
# all packages (like 'app', 'app/ai', etc.)
# have an '__init__.py' file.
print("Attempting to import Decision Engine...")
from app.ai.intent_classification.decision_engine import get_intent_classification
print("Successfully imported Decision Engine.")

# --- Qdrant Client Import ---
from qdrant_client import QdrantClient, models
# --- End Qdrant Client Import ---

# Load environment variables
load_dotenv()

# --- Qdrant Configuration ---
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
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
        # Try to connect
        client = QdrantClient(QDRANT_URL, timeout=10) # Set a timeout
        client.get_collections() # Make an actual test call
        
        # If the call succeeds:
        qdrant_client = client
        print(f"✅ Successfully connected to Qdrant on attempt {i+1}.")
        break # Exit the loop
        
    except Exception as e:
        print(f"Attempt {i+1} failed: Could not connect to Qdrant. Is the Docker container running?")
        print(f"   Error detail: {e}")
        if i < retries - 1:
            print(f"   Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        else:
            print(f"🛑 FAILED to initialize Qdrant client after {retries} attempts.")
            # qdrant_client will remain None, and the app will log errors in lifespan

# --- End Qdrant Client Initialization ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    print("🚀 Starting Intent Classification API...")
    
    # --- Initialize the Decision Engine singleton ---
    # This call will load all models on startup
    try:
        get_intent_classification("warm up")
        print("✅ Models loaded and Decision Engine is warm.")
    except Exception as e:
        print(f"🛑 ERROR during model warmup: {e}")

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
            print(f"✅ Qdrant collection '{PRODUCT_COLLECTION_NAME}' created.")
        except Exception as e:
            # This is a common, expected error if the collection already exists
            if "already exists" in str(e).lower() or "exists" in str(e).lower():
                print(f"✅ Qdrant collection '{PRODUCT_COLLECTION_NAME}' already exists.")
            else:
                # This would be an unexpected error (e.g., Qdrant server is down)
                print(f"🛑 ERROR: Could not create/verify Qdrant collection: {e}")
    else:
        print("🛑 Qdrant client not initialized, skipping collection creation.")
    # --- End Qdrant Collection Initialization ---
        
    print("✅ Intent Classification API started successfully!")
    yield
    print("🛑 Shutting down Intent Classification API...")
    print("✅ Intent Classification API shut down successfully!")


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
        "message": "🤖 Hybrid Intent Classification System is running!"
    }


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """Detailed health check endpoint."""
    # Check Qdrant connection status
    qdrant_status = "disconnected"
    if qdrant_client:
        try:
            qdrant_client.get_collections() # A simple health check operation
            qdrant_status = "connected"
        except Exception:
            qdrant_status = "unhealthy"

    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "services": {
            "qdrant": qdrant_status,
            "redis": "connected",     # This would be dynamic
            "openai": "available"     # This would be dynamic
        },
        "version": os.getenv("APP_VERSION", "1.0.0")
    }

# --- START OF CLASSIFICATION ENDPOINT ---

# 1. Define the input data model for classification
class ClassificationInput(BaseModel):
    text: str
    # You could add more fields here, like user_id, session_id, etc.

# 2. Create the classification POST endpoint
@app.post("/classify", tags=["Intent Classification"])
async def classify_intent(user_input: ClassificationInput) -> Dict[str, Any]:
    """
    Receives user text and returns the classified intent.
    
    This is the main endpoint for the intent classification service.
    """
    
    print(f"Received text for classification: {user_input.text}")
    
    try:
        # The classification function is synchronous (not async)
        result = get_intent_classification(user_input.text)
        
        # Add original text to the response
        result["original_text"] = user_input.text

        # --- TODO: Add Qdrant Search Logic ---
        # If the intent is "find_product" or similar,
        # you would now:
        # 1. Get the embedding for user_input.text (from your DecisionEngine or another service)
        # 2. Use qdrant_client.search(...) to find matching products
        # 3. Add the search results to the 'result' dictionary
        # --- End TODO ---
        
        return result

    except Exception as e:
        # Log the error for debugging
        print(f"🛑 ERROR: An error occurred in /classify: {e}")
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


# Include API routers (uncomment when routers are created)
# app.include_router(intent.router, prefix="/api/v1/intent", tags=["Intent Classification"])
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
