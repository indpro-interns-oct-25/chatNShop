"""
Intent Classification API - Main Application Entry Point
"""
import os
import time
from contextlib import asynccontextmanager
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from app.api.v1 import intent
from app.ai.intent_classification.decision_engine import get_intent_classification
from app.api.v1.intent import router as intent_router
from app.services import classify_intent as run_intent_pipeline
print("Successfully imported Decision Engine.")

# --- Qdrant Client Import ---
from qdrant_client import QdrantClient, models


load_dotenv()


QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
PRODUCT_COLLECTION_NAME = "chatnshop_products"
VECTOR_SIZE = 384


print(f"Attempting to connect to Qdrant at {QDRANT_URL}...")
qdrant_client = None
for attempt in range(1, 6):
    try:
        client = QdrantClient(QDRANT_URL, timeout=10)
        client.get_collections()
        qdrant_client = client
        print(f"Successfully connected to Qdrant on attempt {attempt}.")
        break
    except Exception as exc:
        print(f"Attempt {attempt} failed: {exc}")
        if attempt == 5:
            print("FAILED to initialize Qdrant client after 5 attempts.")
        else:
            time.sleep(3)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Intent Classification API...")
    try:
        get_intent_classification("warm up")
        print("Decision Engine warmed up.")
    except Exception as exc:
        print(f"ERROR during model warmup: {exc}")

    if qdrant_client:
        print(f"Ensuring Qdrant collection '{PRODUCT_COLLECTION_NAME}' exists...")
        try:
            qdrant_client.create_collection(
                collection_name=PRODUCT_COLLECTION_NAME,
                vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE),
            )
            print(f"Collection '{PRODUCT_COLLECTION_NAME}' created.")
        except Exception as exc:
            msg = str(exc).lower()
            if "exists" in msg:
                print(f"Collection '{PRODUCT_COLLECTION_NAME}' already exists.")
            else:
                print(f"ERROR creating collection: {exc}")
    else:
        print("Qdrant client unavailable; skipping collection creation.")

    yield

    print("Shutting down Intent Classification API...")


app = FastAPI(
    title=os.getenv("APP_NAME", "Intent Classification API"),
    version=os.getenv("APP_VERSION", "1.0.0"),
    description="Hybrid rule-based + LLM intent classification backend for chatNShop",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=os.getenv("ALLOWED_METHODS", "GET,POST,PUT,DELETE").split(","),
    allow_headers=os.getenv("ALLOWED_HEADERS", "*").split(","),
)


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
            "redis": "connected",
            "openai": "available",
        },
        "version": os.getenv("APP_VERSION", "1.0.0"),
    }


class ClassificationInput(BaseModel):
    text: str


@app.post("/classify", tags=["Intent Classification"])
async def classify_intent(user_input: ClassificationInput) -> Dict[str, Any]:
    print(f"Received text for classification: {user_input.text}")
    try:
        result = run_intent_pipeline(user_input.text)
        result["original_text"] = user_input.text
        return result
    except Exception as exc:
        print(f"ERROR in /classify: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Classification Failed",
                "message": "An internal error occurred while processing the request.",
                "detail": str(exc),
            },
        )


# Include API routers
app.include_router(intent_router)

# app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["Feedback"])
# app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
# app.include_router(experiments.router, prefix="/api/v1/experiments", tags=["Experiments"])


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


def run() -> None:
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 8000)),
        reload=False,
        workers=int(os.getenv("WORKERS", 1)),
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )


if __name__ == "__main__":
    run()
