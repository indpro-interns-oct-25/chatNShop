import time
from typing import Callable, Any

from .metrics import (
    MODEL_CALL_COUNT,
    MODEL_CALL_LATENCY,
    MODEL_CALL_ERRORS,
    MODEL_CALL_COST,
    CONFIDENCE_HIST,
    INTENT_COUNTER,
)

def instrument_model_call(model_name: str):
    """
    Usage:
      @instrument_model_call("gpt-4o")
      def call_model(...): ...
    """
    def decorator(fn: Callable):
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = fn(*args, **kwargs)
            except Exception as e:
                MODEL_CALL_ERRORS.labels(model=model_name, error_type=type(e).__name__).inc()
                raise
            finally:
                elapsed = time.time() - start
                MODEL_CALL_LATENCY.labels(model=model_name).observe(elapsed)
                MODEL_CALL_COUNT.labels(model=model_name).inc()
            try:
                # record optional metrics
                if isinstance(result, dict):
                    confidence = result.get("confidence")
                    if confidence is not None:
                        try:
                            CONFIDENCE_HIST.observe(float(confidence))
                        except Exception:
                            pass

                    pred_intent = result.get("action_code") or result.get("intent")
                    if pred_intent:
                        INTENT_COUNTER.labels(intent=str(pred_intent)).inc()

                    estimated_cost_cents = result.get("estimated_cost_cents")
                    if estimated_cost_cents is not None:
                        MODEL_CALL_COST.labels(model=model_name).inc(float(estimated_cost_cents))
            except Exception:
                # Do not crash if instrumentation fails
                pass
            return result
        return wrapper
    return decorator
