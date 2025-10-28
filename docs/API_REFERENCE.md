# Keyword Matching System - API Documentation

**Task:** CNS-16 - API Documentation Deliverable  
**Date:** October 28, 2025  
**Version:** 1.0

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Core APIs](#core-apis)
3. [HTTP Endpoints](#http-endpoints)
4. [Response Formats](#response-formats)
5. [Error Handling](#error-handling)
6. [Rate Limits & Performance](#rate-limits--performance)

---

## 🎯 Overview

This document provides complete API reference for the Rule-Based Keyword Matching System. The system exposes both Python APIs (for internal use) and HTTP REST APIs (for external clients).

---

## 🐍 Core Python APIs

### 1. KeywordMatcher Class

#### Constructor
```python
from app.ai.intent_classification.keyword_matcher import KeywordMatcher

matcher = KeywordMatcher()
```

**Parameters:** None  
**Returns:** KeywordMatcher instance  
**Raises:** 
- `FileNotFoundError`: If keyword JSON files are missing
- `JSONDecodeError`: If keyword files are malformed

**Example:**
```python
try:
    matcher = KeywordMatcher()
    print("✅ Matcher initialized successfully")
except Exception as e:
    print(f"❌ Initialization failed: {e}")
```

---

#### Method: `search(query, top_n=3)`

Performs keyword-based intent matching on user query.

**Signature:**
```python
def search(self, query: str, top_n: int = 3) -> List[Dict[str, Any]]
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | str | Yes | - | User input text to classify |
| `top_n` | int | No | 3 | Maximum number of results to return |

**Returns:** List of dictionaries with the following structure:
```python
[
    {
        "id": str,              # Intent action code (e.g., "ADD_TO_CART")
        "intent": str,          # Same as id (for compatibility)
        "score": float,         # Confidence score (0.0 to 1.0)
        "source": str,          # Always "keyword"
        "match_type": str,      # "exact", "regex", or "partial"
        "matched_text": str     # The keyword pattern that matched
    }
]
```

**Match Type Details:**
- **exact**: Perfect match with a keyword phrase (score = 1.0)
- **regex**: Matches a regex pattern (score = 0.7-0.99)
- **partial**: Token overlap with keywords (score = 0.5-0.85)

**Examples:**

*Example 1: Exact Match*
```python
matcher = KeywordMatcher()
results = matcher.search("add to cart")

# Output:
[{
    "id": "ADD_TO_CART",
    "intent": "ADD_TO_CART",
    "score": 1.0,
    "source": "keyword",
    "match_type": "exact",
    "matched_text": "add to cart"
}]
```

*Example 2: Multiple Results*
```python
results = matcher.search("search for shoes", top_n=3)

# Output:
[
    {
        "id": "SEARCH_PRODUCT",
        "score": 0.95,
        "match_type": "partial",
        "matched_text": "search"
    },
    {
        "id": "VIEW_PRODUCT",
        "score": 0.6,
        "match_type": "partial",
        "matched_text": "shoes"
    }
]
```

*Example 3: No Match*
```python
results = matcher.search("xyz123")

# Output:
[]  # Empty list when no matches found
```

**Raises:**
- `TypeError`: If query is not a string
- `ValueError`: If top_n < 1

**Performance:**
- Average latency: 3-8ms
- Throughput: ~200 queries/second
- Memory: ~50MB (keyword cache)

---

### 2. match_keywords Function

Functional API for keyword matching (used internally by KeywordMatcher).

**Signature:**
```python
def match_keywords(
    text: str,
    *,
    normalize: Optional[Callable[[str], str]] = None,
    top_n: int = 1
) -> List[Dict]
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `text` | str | Yes | - | User input text |
| `normalize` | Callable | No | `normalize_text` | Custom normalization function |
| `top_n` | int | No | 1 | Max results |

**Returns:** Same format as `KeywordMatcher.search()`

**Example with Custom Normalization:**
```python
from app.ai.intent_classification.keyword_matcher import match_keywords

def custom_normalize(text):
    return text.lower().replace("shopping", "cart")

results = match_keywords(
    "add to shopping",
    normalize=custom_normalize,
    top_n=2
)
```

---

### 3. DecisionEngine Class

Orchestrates hybrid search with keyword priority.

#### Constructor
```python
from app.ai.intent_classification.decision_engine import DecisionEngine

engine = DecisionEngine()
```

**Parameters:** None  
**Returns:** DecisionEngine instance  
**Side Effects:** Initializes KeywordMatcher and EmbeddingMatcher

---

#### Method: `search(query)`

Performs hybrid intent classification with fallback logic.

**Signature:**
```python
def search(self, query: str) -> Dict[str, Any]
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | str | Yes | User input text |

**Returns:**
```python
{
    "status": str,           # Classification status
    "intent": {
        "id": str,           # Intent action code
        "intent": str,       # Same as id
        "score": float,      # Final blended score
        "source": str,       # "keyword", "embedding", or "fallback"
        "match_type": str,   # Only for keyword matches
        "blend_scores": {    # Only for blended results
            "kw": float,
            "emb": float,
            "consensus_bonus": float,
            "confidence_bonus": float
        }
    }
}
```

**Status Values:**
- `CONFIDENT_KEYWORD`: High-confidence keyword match (≥0.85)
- `CONFIDENT_BLENDED`: Blended result passes confidence check
- `FALLBACK_EMBEDDING`: Lower threshold embedding match
- `FALLBACK_KEYWORD`: Lower threshold keyword match
- `FALLBACK_GENERIC`: Generic search fallback

**Example:**
```python
engine = DecisionEngine()
result = engine.search("add wireless headphones to cart")

# Output:
{
    "status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "ADD_TO_CART",
        "score": 1.0,
        "source": "keyword",
        "match_type": "partial"
    }
}
```

---

### 4. get_intent_classification Function

Main entry point used by FastAPI endpoints.

**Signature:**
```python
def get_intent_classification(query: str) -> Dict[str, Any]
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | str | Yes | User input text |

**Returns:**
```python
{
    "classification_status": str,  # Status from DecisionEngine
    "intent": {
        "id": str,
        "score": float,
        ...
    },
    "source": "hybrid_decision_engine"
}
```

**Special Behavior:**
- `query="warm up"`: Returns `{"status": "warmed_up"}` (health check)

**Example:**
```python
from app.ai.intent_classification.decision_engine import get_intent_classification

result = get_intent_classification("track my order")

# Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "TRACK_ORDER",
        "score": 1.0
    },
    "source": "hybrid_decision_engine"
}
```

---

### 5. detect_intent Function (Ambiguity Resolver)

Handles ambiguous and multi-intent queries.

**Signature:**
```python
def detect_intent(user_input: str) -> Dict[str, Any]
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_input` | str | Yes | User query |

**Returns:**
```python
# Single intent
{
    "action": str,              # Intent action code
    "confidence": float,        # 0.0 to 1.0
    "possible_intents": dict    # All detected intents
}

# Ambiguous (multiple intents)
{
    "action": "AMBIGUOUS",
    "possible_intents": {
        "ADD_TO_CART": 0.7,
        "SEARCH_PRODUCT": 0.65
    }
}

# Unclear (low confidence)
{
    "action": "UNCLEAR",
    "possible_intents": {
        "SEARCH_PRODUCT": 0.3
    }
}
```

**Example:**
```python
from app.ai.intent_classification.ambiguity_resolver import detect_intent

# Single clear intent
result = detect_intent("add to cart")
# {"action": "ADD_TO_CART", "confidence": 0.95}

# Ambiguous
result = detect_intent("add shoes and track order")
# {"action": "AMBIGUOUS", "possible_intents": {...}}

# Unclear
result = detect_intent("hmm something")
# {"action": "UNCLEAR", "possible_intents": {...}}
```

---

## 🌐 HTTP REST APIs

### Base URL
```
http://localhost:8000/api/v1
```

### Endpoint: Classify Intent

**POST** `/intent/classify`

Classifies user intent using hybrid keyword + embedding approach.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "query": "string (required, min 1 char, max 500 chars)"
}
```

**Success Response (200 OK):**
```json
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "ADD_TO_CART",
        "intent": "ADD_TO_CART",
        "score": 1.0,
        "source": "keyword",
        "match_type": "exact"
    },
    "source": "hybrid_decision_engine"
}
```

**Error Responses:**

*400 Bad Request* - Invalid input
```json
{
    "detail": "Query is required and must be a non-empty string"
}
```

*422 Unprocessable Entity* - Validation error
```json
{
    "detail": [
        {
            "loc": ["body", "query"],
            "msg": "field required",
            "type": "value_error.missing"
        }
    ]
}
```

*500 Internal Server Error* - System error
```json
{
    "detail": "Intent classification failed: <error message>"
}
```

**cURL Examples:**

*Example 1: Simple Query*
```bash
curl -X POST "http://localhost:8000/api/v1/intent/classify" \
  -H "Content-Type: application/json" \
  -d '{"query": "add to cart"}'
```

*Example 2: Complex Query*
```bash
curl -X POST "http://localhost:8000/api/v1/intent/classify" \
  -H "Content-Type: application/json" \
  -d '{"query": "I want to add wireless headphones to my shopping cart"}'
```

*Example 3: Health Check*
```bash
curl -X POST "http://localhost:8000/api/v1/intent/classify" \
  -H "Content-Type: application/json" \
  -d '{"query": "warm up"}'

# Response:
{"status": "warmed_up"}
```

**Python Requests Example:**
```python
import requests

url = "http://localhost:8000/api/v1/intent/classify"
payload = {"query": "track my order"}
headers = {"Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)

if response.status_code == 200:
    data = response.json()
    intent_id = data["intent"]["id"]
    score = data["intent"]["score"]
    print(f"Intent: {intent_id}, Confidence: {score}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

---

## 📊 Response Formats

### Intent Object Schema

```json
{
    "id": "string",              // Intent action code (required)
    "intent": "string",          // Same as id (required)
    "score": "number",           // 0.0 to 1.0 (required)
    "source": "string",          // "keyword", "embedding", "fallback" (required)
    "match_type": "string",      // "exact", "regex", "partial" (optional)
    "matched_text": "string",    // Matched keyword pattern (optional)
    "blend_scores": {            // Only for blended results (optional)
        "kw": "number",
        "emb": "number",
        "consensus_bonus": "number",
        "confidence_bonus": "number"
    },
    "match_count": "number",     // Number of matchers that agreed (optional)
    "max_individual_score": "number"  // Highest individual score (optional)
}
```

### Classification Status Values

| Status | Meaning | Score Range | Source |
|--------|---------|-------------|--------|
| `CONFIDENT_KEYWORD` | High-confidence keyword match | ≥0.85 | Keyword only |
| `CONFIDENT_BLENDED` | High-confidence hybrid result | ≥0.6 | Keyword + Embedding |
| `FALLBACK_EMBEDDING` | Lower threshold embedding | 0.3-0.6 | Embedding only |
| `FALLBACK_KEYWORD` | Lower threshold keyword | 0.3-0.6 | Keyword only |
| `FALLBACK_GENERIC` | Generic search fallback | 0.1 | Fallback |

---

## ⚠️ Error Handling

### Error Types

#### 1. Input Validation Errors
```python
# Empty query
result = matcher.search("")
# Returns: []

# Non-string input
result = matcher.search(123)
# Raises: TypeError
```

#### 2. Initialization Errors
```python
# Missing keyword files
matcher = KeywordMatcher()
# Raises: FileNotFoundError
```

#### 3. Runtime Errors
```python
# DecisionEngine not initialized
result = get_intent_classification("query")
# Raises: RuntimeError("DecisionEngine is not initialized")
```

### Best Practices

**1. Always Check for Empty Results:**
```python
results = matcher.search(user_query)
if not results:
    # Handle no match case
    print("No intent matched, using fallback")
```

**2. Validate Query Length:**
```python
MAX_QUERY_LENGTH = 500

if len(query) > MAX_QUERY_LENGTH:
    query = query[:MAX_QUERY_LENGTH]
    print("Query truncated to 500 characters")
```

**3. Handle Exceptions:**
```python
try:
    result = get_intent_classification(query)
    intent_id = result["intent"]["id"]
except RuntimeError as e:
    print(f"System error: {e}")
    intent_id = "SEARCH_PRODUCT"  # Safe fallback
except Exception as e:
    print(f"Unexpected error: {e}")
    intent_id = "SEARCH_PRODUCT"
```

---

## 📈 Rate Limits & Performance

### Performance Characteristics

| Metric | Keyword Only | Hybrid (with embedding) |
|--------|-------------|------------------------|
| Average Latency | 3-8ms | 50-150ms |
| P95 Latency | 12ms | 200ms |
| P99 Latency | 20ms | 350ms |
| Throughput | 200 req/sec | 50 req/sec |
| Memory Usage | 50MB | 500MB |

### Optimization Tips

**1. Use Priority Threshold to Skip Embeddings:**
```python
# In config.py
PRIORITY_THRESHOLD = 0.85  # Higher = more keyword-only results
```

**2. Cache Results for Repeated Queries:**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_classification(query: str):
    return get_intent_classification(query)
```

**3. Batch Processing:**
```python
# Process multiple queries efficiently
queries = ["query1", "query2", "query3"]
results = [get_intent_classification(q) for q in queries]
```

---

## 🔒 Security Considerations

### Input Sanitization
- Max query length: 500 characters
- Special characters normalized automatically
- No SQL injection risk (no database queries)

### Rate Limiting (Recommended)
```python
from fastapi import Depends
from fastapi_limiter.depends import RateLimiter

@app.post("/api/v1/intent/classify", dependencies=[Depends(RateLimiter(times=100, seconds=60))])
async def classify_intent(request: IntentRequest):
    # Rate limited to 100 requests per minute
    pass
```

---

## 📝 Changelog

### Version 1.0 (October 28, 2025)
- Initial API documentation
- Core Python APIs documented
- HTTP REST endpoints documented
- Response formats standardized
- Error handling guide added

---

**For More Information:**
- [Main Documentation](KEYWORD_MATCHING_GUIDE.md)
- [Keyword Maintenance Guide](KEYWORD_MAINTENANCE_GUIDE.md)
- [Performance Tuning Guide](PERFORMANCE_TUNING_GUIDE.md)
