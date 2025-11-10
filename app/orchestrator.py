from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import httpx
import os
from loguru import logger

from app.config import Settings, build_pg_dsn
from app.db.postgres import init_pool, close_pool
from app.llm_connectors.shopify_client import ShopifyClient

# -----------------------------------------------------------------------------
# FASTAPI APP CONFIGURATION
# -----------------------------------------------------------------------------
app = FastAPI(
    title="E-commerce Orchestrator API",
    description="Routes user input → Intent Classifier → Appropriate Backend",
    version="1.0.0"
)


# -----------------------------------------------------------------------------
# STARTUP / SHUTDOWN
# -----------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup() -> None:
    settings = Settings()
    app.state.settings = settings

    # Init Postgres (best-effort)
    dsn = build_pg_dsn(settings)
    if dsn:
        await init_pool(dsn)
    else:
        logger.warning("No PostgreSQL DSN configured, Shopify logs will use JSONL fallback")

    # Init Shopify client (if configured)
    if settings.shopify_shop_domain and settings.shopify_access_token:
        app.state.shopify_client = ShopifyClient(
            shop_domain=settings.shopify_shop_domain,
            access_token=settings.shopify_access_token,
            api_version=settings.shopify_api_version,
            timeout_seconds=settings.shopify_timeout_seconds,
            log_response_bodies=settings.shopify_log_response_bodies,
        )
        logger.info("Shopify client initialized")
    else:
        app.state.shopify_client = None
        logger.warning("Shopify credentials not configured; Shopify calls are disabled")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    # Close Shopify client
    client: ShopifyClient | None = getattr(app.state, "shopify_client", None)
    if client:
        await client.aclose()
    # Close PG pool
    await close_pool()

# -----------------------------------------------------------------------------
# SERVICE URL CONFIGURATION
# -----------------------------------------------------------------------------
# Intent Classifier API (Your main.py service)
INTENT_CLASSIFIER_URL = os.getenv("INTENT_CLASSIFIER_URL", "http://localhost:8000/classify")

# Example backend APIs
SEARCH_API_URL = os.getenv("SEARCH_API_URL", "http://localhost:8002/search")
CART_API_URL = os.getenv("CART_API_URL", "http://localhost:8003/cart")
ORDER_API_URL = os.getenv("ORDER_API_URL", "http://localhost:8004/order")
CHECKOUT_API_URL = os.getenv("CHECKOUT_API_URL", "http://localhost:8005/checkout")

# -----------------------------------------------------------------------------
# REQUEST MODEL
# -----------------------------------------------------------------------------
class UserQuery(BaseModel):
    text: str

# -----------------------------------------------------------------------------
# ORCHESTRATOR ENDPOINT
# -----------------------------------------------------------------------------
@app.post("/orchestrate")
async def orchestrate(query: UserQuery):
    """
    Main orchestration endpoint.
    1️⃣ Accepts user input.
    2️⃣ Calls intent classifier.
    3️⃣ Routes request to the proper backend based on intent.
    """

    # STEP 1: Call the intent classifier
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            classifier_response = await client.post(INTENT_CLASSIFIER_URL, json={"text": query.text})
            classifier_response.raise_for_status()
            intent_data = classifier_response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Intent classification failed: {str(e)}")

    # STEP 2: Parse classifier response
    action_code = intent_data.get("action_code", "UNKNOWN_INTENT")
    confidence = float(intent_data.get("confidence_score", 0))
    entities = intent_data.get("entities", {})
    status = intent_data.get("status", "UNKNOWN")

    # STEP 3: Handle low-confidence cases
    if confidence < 0.6:
        return {
            "status": "LOW_CONFIDENCE",
            "message": "I'm not sure what you mean. Could you rephrase?",
            "intent_result": intent_data
        }

    # STEP 4: Decide routing logic
    backend_url = None
    action_label = None

    if action_code.startswith("SEARCH_"):
        backend_url = SEARCH_API_URL
        action_label = "Product Search"
    elif action_code in ["ADD_TO_CART", "REMOVE_FROM_CART", "VIEW_CART"]:
        backend_url = CART_API_URL
        action_label = "Cart Management"
    elif action_code.startswith("ORDER_") or action_code in ["TRACK_SHIPMENT", "DELIVERY_STATUS"]:
        backend_url = ORDER_API_URL
        action_label = "Order Management"
    elif action_code.startswith("CHECKOUT_"):
        backend_url = CHECKOUT_API_URL
        action_label = "Checkout"
    else:
        return {
            "status": "UNKNOWN_INTENT",
            "message": f"No routing rule found for intent '{action_code}'",
            "intent_result": intent_data
        }

    # STEP 5: Call the selected backend API
    backend_response_data = {}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            backend_response = await client.post(backend_url, json=entities)
            if backend_response.is_success:
                backend_response_data = backend_response.json()
            else:
                backend_response_data = {"error": f"Backend responded with {backend_response.status_code}"}
    except Exception as e:
        backend_response_data = {"error": f"Failed to call backend: {str(e)}"}

    # STEP 6: Return unified response
    return {
        "status": "SUCCESS",
        "intent": action_code,
        "confidence": confidence,
        "entities": entities,
        "classified_status": status,
        "orchestrator_message": f"Intent '{action_code}' routed to {action_label} backend.",
        "backend_response": backend_response_data
    }


# -----------------------------------------------------------------------------
# HEALTH CHECK ENDPOINT
# -----------------------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "Orchestrator API",
        "message": "The Orchestrator is running and ready to route requests."
    }


# -----------------------------------------------------------------------------
# DEBUG: Basic Shopify ping to verify logging
# -----------------------------------------------------------------------------
@app.get("/debug/shopify/ping")
async def shopify_ping(request: Request):
    client: ShopifyClient | None = getattr(app.state, "shopify_client", None)
    if not client:
        raise HTTPException(status_code=503, detail="Shopify client not configured")
    # GET shop info as a lightweight call
    path = f"/admin/api/{app.state.settings.shopify_api_version}/shop.json"
    try:
        resp = await client.get(path)
        data = resp.json()
        return {"status": "ok", "shop": data.get("shop", {}).get("name")}
    except Exception as e:
        # Still logged with timestamps by the client
        raise HTTPException(status_code=502, detail=f"Shopify ping failed: {str(e)}")
