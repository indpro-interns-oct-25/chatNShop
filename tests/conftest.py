# tests/conftest.py
import os
import sys
import pytest

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.fixture(scope="session")
def sample_queries():
    return [
        "Add this to my cart",
        "Find iPhone covers",
        "Show specs of laptop",
        "Go to checkout",
        "Compare phones",
        "What's the refund policy",
    ]
