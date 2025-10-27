"""
Intent Classification API - Main Application Entry Point

This is the main FastAPI application that serves as the entry point for the
hybrid rule-based + LLM intent classification backend.
"""

from contextlib import asynccontextmanager
from typing import Dict, Any
import os
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Load environment variables
load_dotenv()

# Import routers (these will be created later)
from app.api.v1 import intent

# Import monitoring and logging
# from app.monitoring.metrics import setup_metrics
# from app.core.config_manager import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    print("🚀 Starting Intent Classification API...")
    
    # Initialize database connections
    # await init_database()
    
    # Initialize Redis connection
    # await init_redis()
    
    # Setup monitoring
    # setup_metrics()
    
    print("✅ Intent Classification API started successfully!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Intent Classification API...")
    
    # Close database connections
    # await close_database()
    
    # Close Redis connection
    # await close_redis()
    
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


# Health check endpoints
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
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",  # This would be dynamic
        "services": {
            "database": "connected",  # This would be dynamic
            "redis": "connected",     # This would be dynamic
            "openai": "available"     # This would be dynamic
        },
        "version": os.getenv("APP_VERSION", "1.0.0")
    }


# Include API routers
app.include_router(intent.router)

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
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("RELOAD", "true").lower() == "true",
        workers=int(os.getenv("WORKERS", 1)),
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )


if __name__ == "__main__":
    run()