"""Intent classification API endpoints."""

from __future__ import annotations

import os
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException

from app.ai.llm_intent.request_handler import RequestHandler
from app.ai.llm_intent.openai_client import OpenAIClient
from app.schemas.llm_intent import (
    LLMIntentRequest,
    LLMIntentResponse,
    LLMIntentSimpleRequest,
)
import logging
from app.monitoring.logging_config import setup_logging
from logging import getLogger

setup_logging()
logger = getLogger("chatnshop")


router = APIRouter(prefix="/api/v1/llm-intent", tags=["LLM Intent"])

# -----------------------------
# Initialize LLM Client
# -----------------------------
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_model = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
openai_temp = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
openai_max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "400"))

internal_logger = logging.getLogger("intent_api")

if openai_api_key:
    client = OpenAIClient(
        api_key=openai_api_key,
        model_name=openai_model,
        temperature=openai_temp,
        max_tokens=openai_max_tokens,
    )
    handler = RequestHandler(client)
    internal_logger.info("✅ LLM Intent handler initialized with OpenAI client")
else:
    internal_logger.warning(
        "⚠️ OPENAI_API_KEY not set, LLM Intent handler will use simulated responses"
    )
    handler = RequestHandler()  # simulated responses


# -----------------------------
# POST /classify endpoint
# -----------------------------
@router.post("/classify", response_model=LLMIntentResponse, summary="Direct LLM intent classification")
async def classify_intent(request: LLMIntentRequest) -> LLMIntentResponse:
    """
    Direct LLM intent classification endpoint.
    """

    # Ensure handler has OpenAI client
    if handler.client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            client = OpenAIClient(
                api_key=api_key,
                model_name=openai_model,
                temperature=openai_temp,
                max_tokens=openai_max_tokens,
            )
            handler.client = client
            internal_logger.info("✅ Re-initialized LLM handler with OpenAI client")
        else:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "OpenAI API not configured",
                    "message": "OPENAI_API_KEY environment variable is not set. Cannot process LLM requests.",
                },
            )

    try:
        # --- Handle Request ---
        result = handler.handle(request)

        # ✅ Ensure result is always a dictionary
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                raise ValueError("Handler returned invalid JSON string")

        if not isinstance(result, dict):
            raise ValueError("Handler output is not a dictionary")

        # --- ✅ NEW: Log query & intent for monitoring ---
        log_data = {
            "user_query": request.user_input,
            "predicted_intent": result.get("intent", {}).get("intent"),
            "confidence": result.get("intent", {}).get("confidence_score"),
            "source": "llm_intent_api",
            "timestamp": datetime.utcnow().isoformat(),
        }

        # ✅ Log to file
        logger.info(json.dumps(log_data, ensure_ascii=False))

        # ✅ Return standardized response
        return LLMIntentResponse(**result)

    except Exception as e:
        internal_logger.error(f"❌ LLM classification error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "LLM processing failed",
                "message": str(e),
            },
        )
