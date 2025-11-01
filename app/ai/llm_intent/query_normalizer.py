"""
Query Normalizer for LLM Response Cache

Normalizes user queries before caching to improve cache hit rates by treating
semantically similar variations as identical queries.
"""

import re
from typing import Optional


class QueryNormalizer:
    """
    Normalizes user queries to improve cache hit rates.
    
    Normalization includes:
    - Lowercasing
    - Whitespace normalization
    - Special character handling
    - Common phrase variations
    """
    
    # Common variations to normalize
    VARIATIONS = {
        "could you": "can you",
        "would you": "can you",
        "please": "",
        "kindly": "",
        "i want to": "i want",
        "i would like to": "i want",
        "i'd like to": "i want",
        "i need to": "i need",
        "show me": "show",
        "tell me": "tell",
        "give me": "give",
    }
    
    def __init__(self):
        """Initialize the query normalizer."""
        # Pre-compile regex patterns for efficiency
        self._multi_space_pattern = re.compile(r'\s+')
        self._special_char_pattern = re.compile(r'[^\w\s\-\'?.,!]')
        self._punctuation_pattern = re.compile(r'([?.!,])\1+')  # Repeated punctuation
    
    def normalize(self, query: str) -> str:
        """
        Normalize a query for caching.
        
        Args:
            query: Raw user query
            
        Returns:
            Normalized query string
            
        Example:
            >>> normalizer = QueryNormalizer()
            >>> normalizer.normalize("Show me RED shoes please!!!")
            'show red shoes'
        """
        if not query or not isinstance(query, str):
            return ""
        
        # Step 1: Convert to lowercase
        normalized = query.lower()
        
        # Step 2: Remove extra/repeated punctuation (keep single instances)
        normalized = self._punctuation_pattern.sub(r'\1', normalized)
        
        # Step 3: Replace common variations
        for original, replacement in self.VARIATIONS.items():
            normalized = normalized.replace(original, replacement)
        
        # Step 4: Remove special characters (keep alphanumeric, spaces, hyphens, apostrophes, basic punctuation)
        normalized = self._special_char_pattern.sub('', normalized)
        
        # Step 5: Normalize whitespace (convert multiple spaces to single space)
        normalized = self._multi_space_pattern.sub(' ', normalized)
        
        # Step 6: Strip leading/trailing whitespace
        normalized = normalized.strip()
        
        # Step 7: Remove trailing punctuation that doesn't add meaning
        normalized = normalized.rstrip('?.!,')
        
        return normalized
    
    def is_cacheable(self, query: str, min_length: int = 3) -> bool:
        """
        Check if a query is worth caching.
        
        Args:
            query: User query
            min_length: Minimum query length for caching (default: 3 chars)
            
        Returns:
            True if query should be cached, False otherwise
        """
        normalized = self.normalize(query)
        
        # Don't cache empty or very short queries
        if len(normalized) < min_length:
            return False
        
        # Don't cache single-word queries (usually too ambiguous)
        if ' ' not in normalized and len(normalized) < 6:
            return False
        
        return True


# Singleton instance
_normalizer_instance: Optional[QueryNormalizer] = None


def get_query_normalizer() -> QueryNormalizer:
    """
    Get or create singleton QueryNormalizer instance.
    
    Returns:
        Singleton QueryNormalizer instance
    """
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = QueryNormalizer()
    return _normalizer_instance


__all__ = ["QueryNormalizer", "get_query_normalizer"]

