"""
Redis connection helper
Handles connecting to Redis with graceful fallback.
"""

import os
import redis
from typing import Optional

# Default Redis URL (you can override via environment variable)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """
    Returns a singleton Redis client.
    Raises an exception if the connection fails.
    """
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    try:
        client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        # test the connection
        client.ping()
        _redis_client = client
        print(f"[Redis] ✅ Connected to {REDIS_URL}")
        return _redis_client
    except Exception as e:
        print(f"[Redis] ⚠️ Could not connect to Redis at {REDIS_URL}: {e}")
        raise

if __name__ == "__main__":
    try:
        client = get_redis_client()
        print("[Test] Redis connection successful ✅")
        print("Ping response:", client.ping())
    except Exception as e:
        print("[Test] Redis connection failed ❌:", e)

