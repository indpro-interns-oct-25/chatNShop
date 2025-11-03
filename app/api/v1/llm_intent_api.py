from fastapi import APIRouter, HTTPException
from app.schemas.llm_intent import LLMIntentRequest, log_sample_query  # ✅ added import
from app.ai.llm_intent import request_handler

router = APIRouter(prefix="/api/v1/llm-intent", tags=["LLM Intent"])


@router.post("/classify")
async def classify_intent(payload: LLMIntentRequest):
    """
    API to classify user intent using LLM-based model.
    """
    try:
        result = request_handler.handle_intent_request(payload.user_input)

        # ✅ Extract relevant info from model output for logging
        user_query = payload.user_input
        predicted_intent = result.get("intent") if isinstance(result, dict) else None
        confidence = result.get("confidence") if isinstance(result, dict) else None
        model_response = result.get("response") if isinstance(result, dict) else str(result)

        # ✅ Log query for monitoring and QA
        log_sample_query(
            user_query=user_query,
            predicted_intent=predicted_intent,
            confidence=confidence,
            model_response=model_response
        )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "LLM processing failed", "message": str(e)}
        )
