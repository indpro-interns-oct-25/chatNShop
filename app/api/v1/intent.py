"""Intent classification API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.ai.llm_intent.request_handler import RequestHandler
from app.schemas.llm_intent import LLMIntentRequest, LLMIntentResponse


router = APIRouter(prefix="/api/v1/llm-intent", tags=["LLM Intent"])

# Instantiate without an actual OpenAI client so we can simulate responses until
# the integration is wired up.
handler = RequestHandler()


@router.post("/classify", response_model=LLMIntentResponse, summary="LLM intent classification")
async def classify_intent(request: LLMIntentRequest) -> LLMIntentResponse:
    """Route rule-based output through the LLM classifier when needed."""

    result = handler.handle(request)

    if not result["triggered"]:
        raise HTTPException(
            status_code=202,
            detail={
                "message": "Rule-based classification retained",
                "metadata": result["metadata"],
            },
        )

    return LLMIntentResponse(**result)
