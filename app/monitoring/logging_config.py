# app/monitoring/logging_config.py
"""
Structured logging configuration for ChatNShop LLM monitoring.

This module sets up:
1. Console logging for runtime visibility.
2. Rotating JSON log file (`logs/sample_queries.jsonl`) to store
   sample user queries and LLM predictions for QA/review.

Each log entry is a single JSON line for easy ingestion or inspection.
"""

import os
import json
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler


# ---------------------------------------------------------------------
# ✅ Custom JSON formatter
# ---------------------------------------------------------------------
class JSONLineFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record):
        # If record.msg is already a dict, log it as structured data
        if isinstance(record.msg, dict):
            payload = record.msg
        else:
            payload = {"message": record.getMessage()}

        # Add metadata
        meta = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
        }
        payload.update(meta)

        return json.dumps(payload, default=str)


# ---------------------------------------------------------------------
# ✅ Logging setup function
# ---------------------------------------------------------------------
def setup_logging():
    """Initialize structured logging for app monitoring and QA."""

    logger = logging.getLogger("chatnshop")
    logger.setLevel(logging.INFO)

    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)

    # Prevent adding handlers multiple times (important for FastAPI reloads)
    if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        # 1️⃣ Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
        )
        logger.addHandler(console_handler)

        # 2️⃣ Rotating JSON file handler for sample queries
        json_handler = RotatingFileHandler(
            "logs/sample_queries.jsonl", maxBytes=5_000_000, backupCount=5
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(JSONLineFormatter())
        logger.addHandler(json_handler)

    return logger


# ---------------------------------------------------------------------
# ✅ Example usage (for reference)
# ---------------------------------------------------------------------
if __name__ == "__main__":
    # Example demo of how to use the logger
    logger = setup_logging()
    sample = {
        "user_query": "Show me red Nike shoes under ₹5000",
        "predicted_intent": "product_search",
        "confidence": 0.92,
        "model_response": "Here are some Nike red shoes under ₹5000.",
        "timestamp": datetime.utcnow().isoformat(),
    }
    logger.info(sample)
    print("✅ Logged one sample query to logs/sample_queries.jsonl")
