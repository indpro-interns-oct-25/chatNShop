"""
Resilient OpenAI Client Stub
----------------------------------
This acts as a safe wrapper around OpenAI or any LLM API,
providing graceful handling for timeouts, rate limits, or connection errors.
"""

import os
import time
import random
from typing import Dict, Any

class ResilientOpenAIClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.retry_limit = 3
        self.cooldown = 2  # seconds

    def call(self, prompt: str) -> Dict[str, Any]:
        """
        Simulates or performs a resilient OpenAI API call.
        Falls back to a dummy response if OpenAI key is not configured.
        """
        if not self.api_key:
            print("⚠ No OPENAI_API_KEY found. Using dummy response.")
            return {
                "action_code": "UNKNOWN_INTENT",
                "confidence": 0.0,
                "source": "mock",
                "message": "Resilient fallback (no API key configured)",
            }

        # Simulated call with retries
        for attempt in range(1, self.retry_limit + 1):
            try:
                # Here you could integrate the real OpenAI client (omitted intentionally)
                print(f"🧠 Simulated LLM call attempt {attempt}: prompt='{prompt}'")
                time.sleep(random.uniform(0.2, 0.5))
                # Return mock structured response
                return {
                    "action_code": "ADD_TO_CART" if "cart" in prompt.lower() else "SEARCH_PRODUCT",
                    "confidence": round(random.uniform(0.6, 0.95), 2),
                    "source": "resilient_stub",
                }
            except Exception as e:
                print(f"❌ LLM call attempt {attempt} failed: {e}")
                time.sleep(self.cooldown)
        # Fallback if all attempts fail
        return {
            "action_code": "UNKNOWN_INTENT",
            "confidence": 0.0,
            "source": "resilient_fallback",
        }


# Expose instance for import convenience
resilient_client = ResilientOpenAIClient()
