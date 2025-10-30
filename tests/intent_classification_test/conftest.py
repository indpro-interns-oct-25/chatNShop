# tests/intent_classification_test/conftest.py
import json
from pathlib import Path
import pytest

@pytest.fixture
def sample_queries():
    """
    Provide sample queries for integration tests.

    Behavior:
    - If tests/intent_classification_test/sample_queries.json exists, load and return its JSON.
    - Else if tests/sample_queries.json exists (alternate location), load and return it.
    - Otherwise return a sensible fallback list of dicts that many intent tests expect.

    Expected shape used by tests (common):
    [
      {"query": "Add to cart this product please", "intent": "ADD_TO_CART"},
      {"query": "Show specs of iPhone", "intent": "PRODUCT_INFO"},
      ...
    ]
    """
    # Possible locations (priority)
    candidates = [
        Path(__file__).parent / "sample_queries.json",
        Path(__file__).parents[1] / "sample_queries.json",
    ]

    for p in candidates:
        try:
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                # If the file contains an object with a "queries" key, accept that too
                if isinstance(data, dict) and "queries" in data:
                    return data["queries"]
                return data
        except Exception:
            # ignore parse errors and try fallback
            break

    # Fallback sample queries (safe defaults covering typical tests)
    return [
        {"query": "Add to cart this product please", "intent": "ADD_TO_CART"},
        {"query": "Can you show specs of iPhone and add to cart?", "intent": "MULTI_INTENT"},
        {"query": "Show me iPhone specs", "intent": "PRODUCT_INFO"},
        {"query": "@@@@add##to###cart$$$$", "intent": "ADD_TO_CART"},
        {"query": "How much does the iPhone cost?", "intent": "PRODUCT_PRICE"},
    ]
