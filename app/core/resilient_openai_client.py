"""
Resilient OpenAI Client Stub
----------------------------------
This acts as a safe wrapper around OpenAI or any LLM API,
providing graceful handling for timeouts, rate limits, or connection errors.
"""

import os
import time
import random
import logging
from datetime import datetime
from typing import Dict, Any

# ✅ Added import for instrumentation
from app.monitoring.model_instrumentation import instrument_model_call

# ✅ Added imports for logging setup
from app.monitoring.logging_config import setup_logging

# ✅ Initialize logging once
setup_logging()
logger = logging.getLogger("chatnshop")


class ResilientOpenAIClient:
    """
    A resilient wrapper around the OpenAI API (or any LLM API) with:
      - Retry logic for transient failures
      - Graceful fallback when API key is missing
      - Instrumentation for observability
      - Centralized logging for model calls
    """

    def __init__(self):
        """Initialize client with API key and retry settings."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.retry_limit = 3
        self.cooldown = 2  # seconds

    # ✅ Added decorator to track metrics
    @instrument_model_call("gpt-4o")
    def call(self, prompt: str) -> Dict[str, Any]:
        """
        Simulates or performs a resilient OpenAI API call.
        Falls back to a dummy response if OpenAI key is not configured.

        Args:
            prompt (str): The input text prompt for the model.

        Returns:
            Dict[str, Any]: A structured response with intent, confidence, and metadata.
        """
        # --------------------------
        # Case 1: No API key → fallback
        # --------------------------
        if not self.api_key:
            print("⚠ No OPENAI_API_KEY found. Using dummy response.")
            result = {
                "action_code": "UNKNOWN_INTENT",
                "confidence": 0.0,
                "source": "mock",
                "message": "Resilient fallback (no API key configured)",
            }

            # ✅ Log sample query
            logger.info({
                "user_query": prompt,
                "predicted_intent": result["action_code"],
                "confidence": result["confidence"],
                "model_response": result["source"],
                "timestamp": datetime.utcnow().isoformat(),
            })
            return result

        # --------------------------
        # Case 2: Simulated call with retries
        # --------------------------
        for attempt in range(1, self.retry_limit + 1):
            try:
                print(f"🧠 Simulated LLM call attempt {attempt}: prompt='{prompt}'")

                # Simulate API latency
                time.sleep(random.uniform(0.2, 0.5))

                # Simulated structured response
                result = {
                    "action_code": "ADD_TO_CART" if "cart" in prompt.lower() else "SEARCH_PRODUCT",
                    "confidence": round(random.uniform(0.6, 0.95), 2),
                    "source": "resilient_stub",
                }

                # ✅ Log successful query
                logger.info({
                    "user_query": prompt,
                    "predicted_intent": result["action_code"],
                    "confidence": result["confidence"],
                    "model_response": result["source"],
                    "timestamp": datetime.utcnow().isoformat(),
                })
                return result

            except Exception as e:
                print(f"❌ LLM call attempt {attempt} failed: {e}")
                time.sleep(self.cooldown)

        # --------------------------
        # Case 3: All retries failed → fallback
        # --------------------------
        result = {
            "action_code": "UNKNOWN_INTENT",
            "confidence": 0.0,
            "source": "resilient_fallback",
        }

        # ✅ Log fallback result
        logger.info({
            "user_query": prompt,
            "predicted_intent": result["action_code"],
            "confidence": result["confidence"],
            "model_response": result["source"],
            "timestamp": datetime.utcnow().isoformat(),
        })
        return result


# ✅ Expose singleton instance for easy imports
resilient_client = ResilientOpenAIClient()
