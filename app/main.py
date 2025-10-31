"""
Intent Classification API - Main Application Entry Point
"""
import sys
import os
import time
from contextlib import asynccontextmanager
from typing import Dict, Any
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel

# --- Imports for classification ---
print("Attempting to import Decision Engine...")
from app.ai.intent_classification.hybrid_classifier import HybridIntentClassifier  # ✅ correct
print("Successfully imported Decision Engine.")

# --- ✅ Corrected Import for classification router ---
from app.api.v1.routes.classification_route import router as classification_router

# --- Qdrant Client Import ---
from qdrant_client import QdrantClient, models

# Load environment variables
load_dotenv()

# --- Qdrant Configuration ---
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
PRODUCT_COLLECTION_NAME = "chatnshop_products"
VECTOR_SIZE = 384
# --- End Qdrant Configuration ---

# --- Initialize Qdrant Client with Retry Logic ---
print(f"Attempting to connect to Qdrant at {QDRANT_URL}...")
qdrant_client = None
retries = 5
wait_time = 3

for i in range(retries):
    try:
        client = QdrantClient(QDRANT_URL, timeout=10)
        client.get_collections()
        qdrant_client = client
        print(f"✅ Successfully connected to Qdrant on attempt {i + 1}.")
        break
    except Exception as e:
        print(f"⚠️ Attempt {i + 1} failed: Could not connect to Qdrant.")
        print(f"   Error: {e}")
        if i < retries - 1:
            print(f"   Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        else:
            print(f"❌ Failed to initialize Qdrant after {retries} attempts.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    print("🚀 Starting Intent Classification API...")

    if qdrant_client:
        print(f"Checking for Qdrant collection '{PRODUCT_COLLECTION_NAME}'...")
        try:
            qdrant_client.create_collection(
                collection_name=PRODUCT_COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=VECTOR_SIZE,
                    distance=models.Distance.COSINE
                ),
            )
            print(f"✅ Qdrant collection '{PRODUCT_COLLECTION_NAME}' created.")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"ℹ️ Qdrant collection '{PRODUCT_COLLECTION_NAME}' already exists.")
            else:
                print(f"❌ ERROR creating collection: {e}")
    else:
        print("⚠️ Qdrant client not initialized, skipping collection check.")

    print("✅ Intent Classification API started successfully!")
    yield
    print("🛑 Shutting down Intent Classification API...")


# --- Create FastAPI App ---
app = FastAPI(
    title=os.getenv("APP_NAME", "Intent Classification API"),
    version=os.getenv("APP_VERSION", "1.0.0"),
    description="Hybrid rule-based + LLM intent classification backend for chatNShop",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# --- Configure CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=os.getenv("ALLOWED_METHODS", "GET,POST,PUT,DELETE").split(","),
    allow_headers=os.getenv("ALLOWED_HEADERS", "*").split(","),
)

# --- ✅ Include Routes ---
app.include_router(classification_router, prefix="/api/v1")

# --- Initialize Classifier ---
classifier = HybridIntentClassifier()  # ✅ correct

# --- Health Endpoints ---
@app.get("/", tags=["Health"])
async def root() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "Intent Classification API",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "message": "Hybrid Intent Classification System is running!",
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

    return {
        "status": "healthy",
        "services": {
            "qdrant": qdrant_status,
            "openai": "available",
        },
        "version": os.getenv("APP_VERSION", "1.0.0"),
    }


# --- Global Exception Handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "path": str(request.url),
        },
    )


# --- App Runner ---
def run():
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 8000)),
        reload=True,
        workers=int(os.getenv("WORKERS", 1)),
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )


if __name__ == "__main__":
    run()
