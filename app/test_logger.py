from monitoring.logging_config import setup_logging
import logging
from datetime import datetime

setup_logging()
logger = logging.getLogger("chatnshop")

logger.info({
    "user_query": "find black shoes",
    "predicted_intent": "SEARCH_PRODUCT",
    "confidence": 0.82,
    "model_response": "resilient_stub",
    "timestamp": datetime.utcnow().isoformat(),
})

# ✅ Ensure logs are written before exit
for handler in logger.handlers:
    handler.flush()

print("✅ Logged one test entry. Check logs/sample_queries.jsonl")
