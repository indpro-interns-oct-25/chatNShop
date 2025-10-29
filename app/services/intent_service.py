"""Service layer orchestrating rule-based and LLM intent classification."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from app.ai.intent_classification.decision_engine import get_intent_classification
from app.core.circuit_breaker import CircuitBreakerOpenError
from app.ai.llm_intent.trigger_manager import LLMTriggerManager
from app.monitoring.metrics import log_latency
from app.schemas.llm_intent import LLMIntentRequest
from app.utils.retry_logic import RetryExceededError

logger = logging.getLogger("app.services.intent_service")

_TRIGGER_MANAGER = LLMTriggerManager()


def classify_intent(
    user_input: str,
    *,
    context_snippets: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run the full hybrid intent classification pipeline."""

    pipeline_start = time.perf_counter()
    context_snippets = list(context_snippets or [])
    metadata_payload: Dict[str, Any] = dict(metadata or {})

    rule_start = time.perf_counter()
    rule_result = get_intent_classification(user_input)
    log_latency("rule_pipeline_latency_ms", start_time=rule_start, tags={"stage": "rule"})

    combined_result: Dict[str, Any] = dict(rule_result)
    combined_result.setdefault("handoff_metadata", {"triggered": False, "reason": None})
    combined_result["llm_triggered"] = False

    if not rule_result.get("needs_llm_review"):
        combined_result["pipeline_latency_ms"] = _pipeline_elapsed(pipeline_start)
        log_latency(
            "intent_pipeline_latency_ms",
            start_time=pipeline_start,
            tags={"llm_triggered": False, "classification_status": combined_result.get("classification_status")},
        )
        return combined_result

    logger.info(
        "Escalating intent classification to LLM fallback",
        extra={
            "trigger_reason": rule_result.get("trigger_reason"),
            "classification_status": rule_result.get("classification_status"),
        },
    )

    llm_request = _build_llm_request(user_input, rule_result, context_snippets, metadata_payload)

    try:
        llm_response = _TRIGGER_MANAGER.invoke(
            llm_request,
            metric_tags={
                "trigger_reason": rule_result.get("trigger_reason") or rule_result.get("classification_status"),
                "llm_triggered": True,
            },
        )
    except CircuitBreakerOpenError as exc:
        _handle_llm_failure(combined_result, "circuit_open", exc)
    except RetryExceededError as exc:
        _handle_llm_failure(combined_result, "retries_exhausted", exc)
    except TimeoutError as exc:
        _handle_llm_failure(combined_result, "timeout", exc)
    except Exception as exc:  # pragma: no cover - defensive guard
        _handle_llm_failure(combined_result, "error", exc)
    else:
        combined_result = _merge_llm_result(combined_result, llm_response, rule_result)
        combined_result["llm_triggered"] = True
        combined_result["handoff_metadata"] = {
            "triggered": True,
            "reason": combined_result.get("trigger_reason"),
        }
        logger.info(
            "LLM fallback completed",
            extra={
                "trigger_reason": combined_result["handoff_metadata"]["reason"],
                "llm_confidence": llm_response.get("confidence"),
            },
        )

    combined_result["pipeline_latency_ms"] = _pipeline_elapsed(pipeline_start)
    log_latency(
        "intent_pipeline_latency_ms",
        start_time=pipeline_start,
        tags={
            "llm_triggered": combined_result.get("llm_triggered", False),
            "classification_status": combined_result.get("classification_status"),
        },
    )
    return combined_result


def _build_llm_request(
    user_input: str,
    rule_result: Dict[str, Any],
    context_snippets: List[str],
    metadata_payload: Dict[str, Any],
) -> LLMIntentRequest:
    metadata_block: Dict[str, Any] = {
        "rule_candidates": rule_result.get("candidates", []),
        "classification_status": rule_result.get("classification_status"),
        "trigger_reason": rule_result.get("trigger_reason"),
        "confidence_gap": rule_result.get("confidence_gap"),
    }
    if metadata_payload:
        metadata_block["client_metadata"] = metadata_payload

    return LLMIntentRequest(
        user_input=user_input,
        rule_intent=rule_result.get("resolved_intent"),
        action_code=rule_result.get("resolved_action_code"),
        top_confidence=float(rule_result.get("top_confidence", 0.0) or 0.0),
        next_best_confidence=float(rule_result.get("next_best_confidence", 0.0) or 0.0),
        is_fallback=bool(rule_result.get("is_fallback", False)),
        context_snippets=[str(snippet) for snippet in context_snippets],
        metadata=metadata_block,
    )


def _merge_llm_result(
    base: Dict[str, Any],
    llm_payload: Dict[str, Any],
    rule_snapshot: Dict[str, Any],
) -> Dict[str, Any]:
    merged = dict(base)

    intent_name = llm_payload.get("intent", "unknown_intent")
    action_code = llm_payload.get("action_code") or intent_name
    confidence = float(llm_payload.get("confidence", 0.0))
    source = llm_payload.get("metadata", {}).get("source", "llm")

    intent_block = {
        "id": action_code,
        "intent": intent_name,
        "action": action_code,
        "score": round(confidence, 4),
        "source": source,
    }

    merged.update(
        {
            "intent": intent_block,
            "candidates": [intent_block],
            "top_confidence": round(confidence, 4),
            "next_best_confidence": round(float(rule_snapshot.get("top_confidence", 0.0) or 0.0), 4),
            "confidence_gap": round(
                round(confidence, 4)
                - round(float(rule_snapshot.get("top_confidence", 0.0) or 0.0), 4),
                4,
            ),
            "resolved_intent": intent_name,
            "resolved_action_code": action_code,
            "is_fallback": llm_payload.get("requires_clarification", False),
            "needs_llm_review": llm_payload.get("requires_clarification", False),
            "classification_status": "LLM_TRIGGERED",
            "trigger_reason": llm_payload.get("metadata", {}).get("trigger_reason", base.get("trigger_reason")),
            "llm_payload": llm_payload,
            "rule_snapshot": {
                "intent": rule_snapshot.get("intent"),
                "candidates": rule_snapshot.get("candidates"),
                "top_confidence": rule_snapshot.get("top_confidence"),
                "next_best_confidence": rule_snapshot.get("next_best_confidence"),
                "classification_status": rule_snapshot.get("classification_status"),
            },
        }
    )

    return merged


def _handle_llm_failure(result: Dict[str, Any], reason: str, exc: BaseException) -> None:
    logger.warning("LLM handoff failed (%s)", reason, exc_info=exc)
    handoff = result.setdefault("handoff_metadata", {})
    handoff.update({"triggered": False, "failure": reason})
    result["llm_triggered"] = False
    result.setdefault("llm_errors", []).append(str(exc))


def _pipeline_elapsed(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


__all__ = ["classify_intent"]
