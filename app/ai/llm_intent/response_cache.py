"""
LLM Response Cache with Semantic Similarity Matching

Implements a Redis-backed cache for LLM responses with semantic similarity-based lookup
using embeddings. This reduces API costs by caching similar queries and improves response times.
"""

import hashlib
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer, util

from app.ai.llm_intent.query_normalizer import get_query_normalizer
from app.ai.llm_intent.cache_metrics import get_cache_metrics

try:
    from app.core.redis_client import get_redis_client
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger("response_cache")


class LLMResponseCache:
    """
    Semantic similarity-based cache for LLM responses.
    
    Features:
    - Redis-backed persistent storage with TTL
    - Embedding-based similarity search for cache lookup
    - Automatic query normalization
    - Configurable similarity threshold
    - In-memory fallback if Redis unavailable
    - Thread-safe operations
    """
    
    def __init__(
        self,
        redis_client=None,
        embedding_model_name: str = "all-MiniLM-L6-v2",
        similarity_threshold: float = None,
        ttl_seconds: int = None,
        max_cache_size: int = None,
        min_query_length: int = None,
        enabled: bool = None
    ):
        """
        Initialize LLM response cache.
        
        Args:
            redis_client: Redis client instance (optional, will create if None)
            embedding_model_name: SentenceTransformer model name (default: all-MiniLM-L6-v2)
            similarity_threshold: Cosine similarity threshold for cache hit (default: 0.95)
            ttl_seconds: Cache TTL in seconds (default: 86400 = 24 hours)
            max_cache_size: Maximum number of cached responses (default: 10000)
            min_query_length: Minimum query length to cache (default: 3)
            enabled: Enable/disable caching (default: True)
        """
        # Configuration from environment or parameters
        self.enabled = enabled if enabled is not None else (
            os.getenv("ENABLE_LLM_CACHE", "true").lower() == "true"
        )
        self.similarity_threshold = similarity_threshold if similarity_threshold is not None else (
            float(os.getenv("LLM_CACHE_SIMILARITY_THRESHOLD", "0.95"))
        )
        self.ttl_seconds = ttl_seconds if ttl_seconds is not None else (
            int(os.getenv("LLM_CACHE_TTL", "86400"))  # 24 hours
        )
        self.max_cache_size = max_cache_size if max_cache_size is not None else (
            int(os.getenv("LLM_CACHE_MAX_SIZE", "10000"))
        )
        self.min_query_length = min_query_length if min_query_length is not None else (
            int(os.getenv("LLM_CACHE_MIN_QUERY_LENGTH", "3"))
        )
        
        # Initialize components
        self.normalizer = get_query_normalizer()
        self.metrics = get_cache_metrics()
        
        # Initialize Redis client
        self.redis_client = None
        self.redis_available = False
        if REDIS_AVAILABLE and self.enabled:
            try:
                self.redis_client = redis_client or get_redis_client()
                self.redis_client.ping()
                self.redis_available = True
                logger.info("✅ LLM Response Cache connected to Redis")
            except Exception as e:
                logger.warning(f"⚠️ Redis not available for LLM cache, using in-memory fallback: {e}")
                self.redis_available = False
        
        # In-memory fallback cache (if Redis unavailable)
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        
        # Initialize embedding model
        logger.info(f"🔄 Loading embedding model '{embedding_model_name}' for cache...")
        try:
            self.embedding_model = SentenceTransformer(embedding_model_name)
            logger.info(f"✅ Embedding model loaded for cache")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            self.enabled = False
            self.embedding_model = None
        
        # Cache key prefix
        self.cache_prefix = "chatns:llm_cache"
        self.index_key = f"{self.cache_prefix}:index"
        
        if self.enabled:
            logger.info(
                f"✅ LLM Response Cache initialized: "
                f"threshold={self.similarity_threshold}, "
                f"ttl={self.ttl_seconds}s, "
                f"redis={'available' if self.redis_available else 'unavailable (using memory)'}"
            )
        else:
            logger.warning("⚠️ LLM Response Cache is DISABLED")
    
    def get(self, query: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached response for a query using semantic similarity.
        
        Args:
            query: User query
            context: Optional context (not used in cache lookup currently)
            
        Returns:
            Cached response dict if found, None otherwise
        """
        if not self.enabled:
            return None
        
        start_time = time.time()
        
        try:
            # Normalize query
            normalized_query = self.normalizer.normalize(query)
            
            # Check if query is cacheable
            if not self.normalizer.is_cacheable(normalized_query, self.min_query_length):
                logger.debug(f"Query not cacheable (too short): '{query}'")
                return None
            
            # Compute query embedding
            query_embedding = self._compute_embedding(normalized_query)
            if query_embedding is None:
                return None
            
            # Search for similar cached queries
            cached_response = self._search_similar(normalized_query, query_embedding)
            
            latency_ms = (time.time() - start_time) * 1000
            
            if cached_response:
                logger.info(f"✅ Cache HIT for query: '{query[:50]}...' (latency: {latency_ms:.2f}ms)")
                self.metrics.record_hit(query=normalized_query, latency_ms=latency_ms)
                
                # Update hit count
                cached_response['_cache_hit_count'] = cached_response.get('_cache_hit_count', 0) + 1
                
                # Return the cached LLM response
                return cached_response.get('response')
            else:
                logger.debug(f"❌ Cache MISS for query: '{query[:50]}...' (latency: {latency_ms:.2f}ms)")
                self.metrics.record_miss(latency_ms=latency_ms)
                return None
                
        except Exception as e:
            logger.error(f"Error during cache lookup: {e}", exc_info=True)
            return None
    
    def set(
        self,
        query: str,
        response: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Cache an LLM response for a query.
        
        Args:
            query: User query
            response: LLM response to cache
            context: Optional context (not used in cache storage currently)
            
        Returns:
            True if cached successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Normalize query
            normalized_query = self.normalizer.normalize(query)
            
            # Check if query is cacheable
            if not self.normalizer.is_cacheable(normalized_query, self.min_query_length):
                logger.debug(f"Query not cacheable (too short): '{query}'")
                return False
            
            # Compute query embedding
            query_embedding = self._compute_embedding(normalized_query)
            if query_embedding is None:
                return False
            
            # Create cache entry
            cache_entry = {
                'query': normalized_query,
                'response': response,
                'embedding': query_embedding.tolist(),
                'timestamp': time.time(),
                '_cache_hit_count': 0
            }
            
            # Generate cache key from embedding hash
            cache_key = self._generate_cache_key(query_embedding)
            
            # Store in Redis or memory
            if self.redis_available and self.redis_client:
                try:
                    # Store cache entry with TTL
                    self.redis_client.setex(
                        cache_key,
                        self.ttl_seconds,
                        json.dumps(cache_entry)
                    )
                    
                    # Add to similarity index (store embedding for similarity search)
                    # Use sorted set with timestamp as score for LRU eviction
                    self.redis_client.zadd(
                        self.index_key,
                        {cache_key: time.time()}
                    )
                    
                    # Limit cache size (remove oldest entries if over limit)
                    cache_size = self.redis_client.zcard(self.index_key)
                    if cache_size > self.max_cache_size:
                        # Remove oldest entries
                        to_remove = cache_size - self.max_cache_size
                        oldest_keys = self.redis_client.zrange(self.index_key, 0, to_remove - 1)
                        if oldest_keys:
                            # Remove from index
                            self.redis_client.zrem(self.index_key, *oldest_keys)
                            # Remove cache entries
                            self.redis_client.delete(*oldest_keys)
                            logger.debug(f"Evicted {len(oldest_keys)} old cache entries (LRU)")
                    
                    logger.debug(f"✅ Cached response for query: '{normalized_query[:50]}...'")
                    return True
                    
                except Exception as e:
                    logger.warning(f"Failed to cache in Redis, falling back to memory: {e}")
                    # Fall through to memory cache
            
            # In-memory fallback
            self._memory_cache[cache_key] = cache_entry
            
            # Limit memory cache size
            if len(self._memory_cache) > self.max_cache_size:
                # Remove oldest entry (FIFO)
                oldest_key = next(iter(self._memory_cache))
                del self._memory_cache[oldest_key]
                logger.debug(f"Evicted old memory cache entry (FIFO)")
            
            logger.debug(f"✅ Cached response in memory for query: '{normalized_query[:50]}...'")
            return True
            
        except Exception as e:
            logger.error(f"Error caching response: {e}", exc_info=True)
            return False
    
    def _compute_embedding(self, query: str) -> Optional[np.ndarray]:
        """
        Compute embedding for a query.
        
        Args:
            query: Normalized query string
            
        Returns:
            Embedding vector as numpy array, or None on error
        """
        if self.embedding_model is None:
            return None
        
        try:
            embedding = self.embedding_model.encode(query, convert_to_tensor=False)
            return np.array(embedding)
        except Exception as e:
            logger.error(f"Failed to compute embedding: {e}")
            return None
    
    def _generate_cache_key(self, embedding: np.ndarray) -> str:
        """
        Generate cache key from embedding vector hash.
        
        Args:
            embedding: Embedding vector
            
        Returns:
            Cache key string
        """
        # Hash the embedding vector to create a stable key
        embedding_bytes = embedding.tobytes()
        embedding_hash = hashlib.sha256(embedding_bytes).hexdigest()[:16]
        return f"{self.cache_prefix}:{embedding_hash}"
    
    def _search_similar(
        self,
        query: str,
        query_embedding: np.ndarray
    ) -> Optional[Dict[str, Any]]:
        """
        Search for similar cached queries using cosine similarity.
        
        Args:
            query: Normalized query string
            query_embedding: Query embedding vector
            
        Returns:
            Cached entry if similar query found, None otherwise
        """
        try:
            # Search Redis cache
            if self.redis_available and self.redis_client:
                return self._search_redis(query, query_embedding)
            else:
                return self._search_memory(query, query_embedding)
        except Exception as e:
            logger.error(f"Error searching cache: {e}", exc_info=True)
            return None
    
    def _search_redis(
        self,
        query: str,
        query_embedding: np.ndarray
    ) -> Optional[Dict[str, Any]]:
        """
        Search Redis cache for similar queries.
        
        Args:
            query: Normalized query string
            query_embedding: Query embedding vector
            
        Returns:
            Cached entry if similar query found, None otherwise
        """
        try:
            # Get all cache keys from index
            cache_keys = self.redis_client.zrange(self.index_key, 0, -1)
            
            if not cache_keys:
                return None
            
            best_match = None
            best_similarity = 0.0
            
            # Compare with all cached embeddings
            for cache_key in cache_keys:
                try:
                    # Get cached entry
                    cached_data = self.redis_client.get(cache_key)
                    if not cached_data:
                        # Entry expired, remove from index
                        self.redis_client.zrem(self.index_key, cache_key)
                        continue
                    
                    cached_entry = json.loads(cached_data)
                    cached_embedding = np.array(cached_entry['embedding'])
                    
                    # Compute cosine similarity
                    similarity = float(util.cos_sim(query_embedding, cached_embedding).item())
                    
                    # Check if above threshold and better than current best
                    if similarity >= self.similarity_threshold and similarity > best_similarity:
                        best_similarity = similarity
                        best_match = cached_entry
                        
                        # If perfect match (similarity ~1.0), return immediately
                        if similarity > 0.99:
                            logger.debug(f"Perfect cache match found: similarity={similarity:.4f}")
                            return best_match
                
                except Exception as e:
                    logger.debug(f"Error checking cache entry {cache_key}: {e}")
                    continue
            
            if best_match:
                logger.debug(
                    f"Cache match found: similarity={best_similarity:.4f}, "
                    f"query='{best_match['query'][:50]}...'"
                )
            
            return best_match
            
        except Exception as e:
            logger.error(f"Error searching Redis cache: {e}")
            return None
    
    def _search_memory(
        self,
        query: str,
        query_embedding: np.ndarray
    ) -> Optional[Dict[str, Any]]:
        """
        Search in-memory cache for similar queries.
        
        Args:
            query: Normalized query string
            query_embedding: Query embedding vector
            
        Returns:
            Cached entry if similar query found, None otherwise
        """
        best_match = None
        best_similarity = 0.0
        
        for cache_key, cached_entry in self._memory_cache.items():
            try:
                cached_embedding = np.array(cached_entry['embedding'])
                
                # Compute cosine similarity
                similarity = float(util.cos_sim(query_embedding, cached_embedding).item())
                
                # Check if above threshold and better than current best
                if similarity >= self.similarity_threshold and similarity > best_similarity:
                    best_similarity = similarity
                    best_match = cached_entry
                    
                    # If perfect match, return immediately
                    if similarity > 0.99:
                        return best_match
            
            except Exception as e:
                logger.debug(f"Error checking memory cache entry: {e}")
                continue
        
        if best_match:
            logger.debug(f"Memory cache match found: similarity={best_similarity:.4f}")
        
        return best_match
    
    def size(self) -> int:
        """
        Get current cache size (number of cached entries).
        
        Returns:
            Number of cached entries
        """
        try:
            if self.redis_available and self.redis_client:
                return int(self.redis_client.zcard(self.index_key))
            else:
                return len(self._memory_cache)
        except Exception as e:
            logger.error(f"Error getting cache size: {e}")
            return 0
    
    def clear(self) -> bool:
        """
        Clear all cached entries.
        
        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            if self.redis_available and self.redis_client:
                # Get all cache keys
                cache_keys = self.redis_client.zrange(self.index_key, 0, -1)
                if cache_keys:
                    # Delete all cache entries
                    self.redis_client.delete(*cache_keys)
                # Clear index
                self.redis_client.delete(self.index_key)
                logger.info("✅ Cleared Redis cache")
            
            # Clear memory cache
            self._memory_cache.clear()
            logger.info("✅ Cleared memory cache")
            
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def invalidate(self, query: str) -> bool:
        """
        Invalidate cached entry for a specific query.
        
        Args:
            query: Query to invalidate
            
        Returns:
            True if invalidated successfully, False otherwise
        """
        try:
            # Normalize query
            normalized_query = self.normalizer.normalize(query)
            
            # Compute embedding
            query_embedding = self._compute_embedding(normalized_query)
            if query_embedding is None:
                return False
            
            # Generate cache key
            cache_key = self._generate_cache_key(query_embedding)
            
            if self.redis_available and self.redis_client:
                # Remove from Redis
                self.redis_client.delete(cache_key)
                self.redis_client.zrem(self.index_key, cache_key)
            
            # Remove from memory
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]
            
            logger.info(f"✅ Invalidated cache for query: '{normalized_query[:50]}...'")
            return True
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return False


# Singleton instance
_cache_instance: Optional[LLMResponseCache] = None


def get_response_cache() -> LLMResponseCache:
    """
    Get or create singleton LLMResponseCache instance.
    
    Returns:
        Singleton LLMResponseCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = LLMResponseCache()
    return _cache_instance


__all__ = ["LLMResponseCache", "get_response_cache"]

