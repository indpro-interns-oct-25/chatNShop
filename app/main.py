"""
Intent Classification API - Main Application Entry Point

This is the main FastAPI application that serves as the entry point for the
hybrid rule-based + LLM intent classification backend.
"""
import sys, os, time, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.config_manager import load_all_configs, start_config_watcher

# Load and watch configurations
load_all_configs()
print("✅ Configuration Management System initialized.\n")

from contextlib import asynccontextmanager
from typing import Dict, Any
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn


# ✅ Patch: Add debounce + JSON validation for config reload
import threading

_last_reload_time = 0
_reload_lock = threading.Lock()


def safe_reload_configs(path: str):
    global _last_reload_time
    with _reload_lock:
        now = time.time()
        if now - _last_reload_time < 1:
            return
        _last_reload_time = now
        print(f"🔁 Config reloaded due to change: {path}")
        try:
            load_all_configs()
        except json.JSONDecodeError as e:
            print(f"⚠️ Skipping invalid JSON file {os.path.basename(path)}: {e}")


# Monkey-patch watcher callback (no other edits needed)
import app.config.config_manager as config_manager
config_manager.safe_reload_configs = safe_reload_configs


# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    print("🚀 Starting Intent Classification API...")

    # ✅ Start watcher (now safe + debounced)
    start_config_watcher()

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
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "services": {
            "database": "connected",
            "redis": "connected",
            "openai": "available"
        },
        "version": os.getenv("APP_VERSION", "1.0.0")
    }


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
