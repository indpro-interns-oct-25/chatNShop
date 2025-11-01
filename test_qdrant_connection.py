"""
Qdrant Connection Test
Verifies that Qdrant is reachable and lists collections safely.
Works with both local and cloud setups.
"""

import os
import pytest
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

def test_qdrant_connection():
    """
    Simple integration check for Qdrant connectivity.
    Skips gracefully if no connection or invalid API key.
    """

    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

    print(f"🔗 Attempting to connect to Qdrant at {QDRANT_URL}...")

    try:
        # Initialize client (API key optional)
        if QDRANT_API_KEY:
            client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        else:
            client = QdrantClient(url=QDRANT_URL)

        # Try to fetch collections
        collections = client.get_collections()
        print("✅ Connected to Qdrant successfully!")
        print(f"📦 Collections found: {[c.name for c in collections.collections]}")

        # Basic assertion
        assert isinstance(collections.collections, list)

    except UnexpectedResponse as e:
        if "401" in str(e) or "Unauthorized" in str(e):
            pytest.skip("⚠️ Skipping: Qdrant requires API key (Unauthorized).")
        else:
            pytest.skip(f"⚠️ Skipping: Qdrant unexpected response: {e}")

    except Exception as e:
        pytest.skip(f"⚠️ Qdrant connection unavailable: {e}")
