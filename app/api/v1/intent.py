"""Intent classification API endpoints."""

from __future__ import annotations

import os
from fastapi import APIRouter, HTTPException

from app.ai.llm_intent.request_handler import RequestHandler
from app.ai.llm_intent.openai_client import OpenAIClient
from app.schemas.llm_intent import LLMIntentRequest, LLMIntentResponse, LLMIntentSimpleRequest
import logging


router = APIRouter(prefix="/api/v1/llm-intent", tags=["LLM Intent"])

# Instantiate with a real OpenAI client if environment variables are set
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_model = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
openai_temp = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
openai_max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "400"))

logger = logging.getLogger("intent_api")

if openai_api_key:
    client = OpenAIClient(
        api_key=openai_api_key,
        model_name=openai_model,
        temperature=openai_temp,
        max_tokens=openai_max_tokens
    )
    handler = RequestHandler(client)
else:
    handler = RequestHandler()


@router.post("/classify", response_model=LLMIntentResponse, summary="LLM intent classification")
async def classify_intent(request: LLMIntentSimpleRequest) -> LLMIntentResponse:
    """Route rule-based output through the LLM classifier when needed."""

    # Build the full request with sensible defaults so the handler logic works
    full = LLMIntentRequest(
        user_input=request.user_input,
        rule_intent=None,
        action_code=None,
        top_confidence=0.0,
        next_best_confidence=0.0,
        is_fallback=False,
        context_snippets=[],
        metadata={},
    )

    result = handler.handle(full)

    if not result.get("triggered", False):
        raise HTTPException(
            status_code=202,
            detail={
                "message": "Rule-based classification retained",
                "metadata": result["metadata"],
            },
        )

    return LLMIntentResponse(**result)
