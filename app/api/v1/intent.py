"""Intent classification API endpoints."""

from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, status

from app.ai.llm_intent.openai_client import OpenAIClient
from app.core.circuit_breaker import CircuitBreakerOpenError
from app.ai.llm_intent.request_handler import RequestHandler
from app.schemas.llm_intent import LLMIntentRequest, LLMIntentResponse


logger = logging.getLogger("app.api.intent")

router = APIRouter(prefix="/api/v1/llm-intent", tags=["LLM Intent"])


def _build_handler() -> RequestHandler:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not configured; using simulated LLM responses")
        return RequestHandler()

    try:
        client = OpenAIClient(api_key=api_key)
        return RequestHandler(client)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to initialize OpenAI client: %s", exc)
        return RequestHandler()


handler: RequestHandler = _build_handler()


@router.post("/classify", response_model=LLMIntentResponse, summary="LLM intent classification")
async def classify_intent(request: LLMIntentRequest) -> LLMIntentResponse:
    """Route rule-based output through the LLM classifier when configuration triggers it."""

    try:
        result = handler.handle(request)
    except CircuitBreakerOpenError as exc:
        logger.error("OpenAI circuit breaker open: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": "LLM temporarily unavailable", "reason": str(exc)},
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unexpected LLM handler failure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "LLM classification failed", "error": str(exc)},
        ) from exc

    if not result["triggered"]:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail={
                "message": "Rule-based classification retained",
                "metadata": result["metadata"],
            },
        )

    return LLMIntentResponse(**result)
