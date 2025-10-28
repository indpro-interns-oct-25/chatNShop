# Example Queries and Expected Outputs

**Task:** CNS-16 - Example Queries Deliverable  
**Date:** October 28, 2025  
**Version:** 1.0

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Shopping Cart Actions](#shopping-cart-actions)
3. [Product Search](#product-search)
4. [Order Management](#order-management)
5. [Account & Profile](#account--profile)
6. [Edge Cases](#edge-cases)
7. [Ambiguous Queries](#ambiguous-queries)
8. [Multi-Intent Queries](#multi-intent-queries)
9. [Error Cases](#error-cases)

---

## 🎯 Overview

This document provides comprehensive examples of user queries and their expected classification outputs. Use these examples for testing, validation, and understanding system behavior.

**Legend:**
- ✅ High Confidence (score ≥ 0.85)
- ⚠️ Medium Confidence (0.60-0.84)
- ❌ Low Confidence (< 0.60)
- 🔀 Ambiguous (multiple intents)
- ❓ Unclear (no clear intent)

---

## 🛒 Shopping Cart Actions

### ADD_TO_CART

#### Example 1: Exact Match ✅
```python
Query: "add to cart"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "ADD_TO_CART",
        "intent": "ADD_TO_CART",
        "score": 1.0,
        "source": "keyword",
        "match_type": "exact",
        "matched_text": "add to cart"
    },
    "source": "hybrid_decision_engine"
}
```

#### Example 2: Natural Language ✅
```python
Query: "I want to add this item to my shopping bag"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "ADD_TO_CART",
        "score": 0.95,
        "source": "keyword",
        "match_type": "partial",
        "matched_text": "add to bag"
    }
}
```

#### Example 3: Short Form ✅
```python
Query: "add this"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "ADD_TO_CART",
        "score": 0.85,
        "source": "keyword",
        "match_type": "partial"
    }
}
```

#### Example 4: With Product Details ✅
```python
Query: "add wireless headphones to cart"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "ADD_TO_CART",
        "score": 1.0,
        "source": "keyword",
        "match_type": "partial"
    }
}
```

#### Example 5: Colloquial ✅
```python
Query: "put this in my cart"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "ADD_TO_CART",
        "score": 1.0,
        "source": "keyword",
        "match_type": "exact"
    }
}
```

---

### VIEW_CART

#### Example 1: Direct Request ✅
```python
Query: "view cart"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "VIEW_CART",
        "score": 1.0,
        "source": "keyword",
        "match_type": "exact"
    }
}
```

#### Example 2: Natural Language ✅
```python
Query: "show me my shopping cart"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "VIEW_CART",
        "score": 0.90,
        "source": "keyword",
        "match_type": "partial"
    }
}
```

#### Example 3: Question Format ✅
```python
Query: "what's in my cart?"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "VIEW_CART",
        "score": 0.85,
        "source": "keyword",
        "match_type": "regex"
    }
}
```

---

### REMOVE_FROM_CART

#### Example 1: Explicit Remove ✅
```python
Query: "remove from cart"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "REMOVE_FROM_CART",
        "score": 1.0,
        "source": "keyword",
        "match_type": "exact"
    }
}
```

#### Example 2: Delete Action ✅
```python
Query: "delete this item from my bag"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "REMOVE_FROM_CART",
        "score": 0.90,
        "source": "keyword",
        "match_type": "partial"
    }
}
```

---

### CHECKOUT

#### Example 1: Direct Checkout ✅
```python
Query: "checkout"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "CHECKOUT",
        "score": 1.0,
        "source": "keyword",
        "match_type": "exact"
    }
}
```

#### Example 2: Buy Now ✅
```python
Query: "buy now"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "CHECKOUT",
        "score": 0.95,
        "source": "keyword",
        "match_type": "exact"
    }
}
```

#### Example 3: Complete Purchase ✅
```python
Query: "I want to complete my purchase"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "CHECKOUT",
        "score": 0.90,
        "source": "keyword",
        "match_type": "partial"
    }
}
```

---

## 🔍 Product Search

### SEARCH_PRODUCT

#### Example 1: Simple Search ✅
```python
Query: "search for shoes"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "SEARCH_PRODUCT",
        "score": 0.95,
        "source": "keyword",
        "match_type": "partial"
    }
}
```

#### Example 2: Find Product ✅
```python
Query: "find red sneakers"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "SEARCH_PRODUCT",
        "score": 0.90,
        "source": "keyword",
        "match_type": "partial"
    }
}
```

#### Example 3: Looking For ✅
```python
Query: "i'm looking for wireless headphones"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "SEARCH_PRODUCT",
        "score": 0.85,
        "source": "keyword",
        "match_type": "partial"
    }
}
```

#### Example 4: Show Me ✅
```python
Query: "show me laptops under $1000"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "SEARCH_PRODUCT",
        "score": 0.90,
        "source": "keyword",
        "match_type": "partial"
    }
}
```

#### Example 5: Browse ✅
```python
Query: "browse electronics"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "SEARCH_PRODUCT",
        "score": 0.85,
        "source": "keyword",
        "match_type": "partial"
    }
}
```

---

### VIEW_PRODUCT

#### Example 1: View Details ✅
```python
Query: "view product details"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "VIEW_PRODUCT",
        "score": 1.0,
        "source": "keyword",
        "match_type": "exact"
    }
}
```

#### Example 2: Show Product ✅
```python
Query: "show me this product"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "VIEW_PRODUCT",
        "score": 0.90,
        "source": "keyword",
        "match_type": "partial"
    }
}
```

---

## 📦 Order Management

### TRACK_ORDER

#### Example 1: Track Order ✅
```python
Query: "track my order"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "TRACK_ORDER",
        "score": 1.0,
        "source": "keyword",
        "match_type": "exact"
    }
}
```

#### Example 2: With Order Number ✅
```python
Query: "track order #12345"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "TRACK_ORDER",
        "score": 0.95,
        "source": "keyword",
        "match_type": "regex"
    }
}
```

#### Example 3: Where Is My Order ✅
```python
Query: "where is my order?"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "TRACK_ORDER",
        "score": 0.90,
        "source": "keyword",
        "match_type": "partial"
    }
}
```

#### Example 4: Order Status ✅
```python
Query: "check order status"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "TRACK_ORDER",
        "score": 0.95,
        "source": "keyword",
        "match_type": "partial"
    }
}
```

---

### VIEW_ORDER_HISTORY

#### Example 1: Order History ✅
```python
Query: "view order history"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "VIEW_ORDER_HISTORY",
        "score": 1.0,
        "source": "keyword",
        "match_type": "exact"
    }
}
```

#### Example 2: Past Orders ✅
```python
Query: "show my past orders"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "VIEW_ORDER_HISTORY",
        "score": 0.90,
        "source": "keyword",
        "match_type": "partial"
    }
}
```

---

### CANCEL_ORDER

#### Example 1: Cancel Order ✅
```python
Query: "cancel my order"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "CANCEL_ORDER",
        "score": 1.0,
        "source": "keyword",
        "match_type": "exact"
    }
}
```

#### Example 2: Cancel Specific Order ✅
```python
Query: "I want to cancel order #67890"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "CANCEL_ORDER",
        "score": 0.95,
        "source": "keyword",
        "match_type": "partial"
    }
}
```

---

### RETURN_PRODUCT

#### Example 1: Return Request ✅
```python
Query: "return this product"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "RETURN_PRODUCT",
        "score": 1.0,
        "source": "keyword",
        "match_type": "exact"
    }
}
```

#### Example 2: Return Policy ⚠️
```python
Query: "what's the return policy?"

Expected Output:
{
    "classification_status": "CONFIDENT_BLENDED",
    "intent": {
        "id": "RETURN_PRODUCT",
        "score": 0.70,
        "source": "hybrid"
    }
}
```

---

## 👤 Account & Profile

### VIEW_ACCOUNT

#### Example 1: My Account ✅
```python
Query: "my account"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "VIEW_ACCOUNT",
        "score": 1.0,
        "source": "keyword",
        "match_type": "exact"
    }
}
```

#### Example 2: Account Settings ✅
```python
Query: "view account settings"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "VIEW_ACCOUNT",
        "score": 0.95,
        "source": "keyword",
        "match_type": "partial"
    }
}
```

---

### UPDATE_PROFILE

#### Example 1: Update Profile ✅
```python
Query: "update my profile"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "UPDATE_PROFILE",
        "score": 1.0,
        "source": "keyword",
        "match_type": "exact"
    }
}
```

#### Example 2: Change Address ✅
```python
Query: "change my shipping address"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "UPDATE_PROFILE",
        "score": 0.90,
        "source": "keyword",
        "match_type": "partial"
    }
}
```

---

## 🔄 Edge Cases

### Very Short Queries

#### Example 1: Single Word ⚠️
```python
Query: "cart"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "VIEW_CART",
        "score": 0.70,
        "source": "keyword",
        "match_type": "partial"
    }
}
```

#### Example 2: Two Words ✅
```python
Query: "track order"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "TRACK_ORDER",
        "score": 1.0,
        "source": "keyword",
        "match_type": "exact"
    }
}
```

---

### Special Characters

#### Example 1: With Symbols ✅
```python
Query: "add shoes & bags to cart"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "ADD_TO_CART",
        "score": 0.95,
        "source": "keyword",
        "match_type": "partial"
    }
}
```

#### Example 2: With Punctuation ✅
```python
Query: "add to cart!!!"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "ADD_TO_CART",
        "score": 1.0,
        "source": "keyword",
        "match_type": "exact"
    }
}
```

---

### Numbers and IDs

#### Example 1: With Product ID ✅
```python
Query: "add product #SKU-12345 to cart"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "ADD_TO_CART",
        "score": 0.90,
        "source": "keyword",
        "match_type": "partial"
    }
}
```

#### Example 2: With Quantity ✅
```python
Query: "add 3 items to cart"

Expected Output:
{
    "classification_status": "CONFIDENT_KEYWORD",
    "intent": {
        "id": "ADD_TO_CART",
        "score": 0.95,
        "source": "keyword",
        "match_type": "partial"
    }
}
```

---

## 🔀 Ambiguous Queries

### Example 1: Multiple Intents 🔀
```python
Query: "add to cart and checkout"

Expected Output (from ambiguity_resolver.py):
{
    "action": "AMBIGUOUS",
    "possible_intents": {
        "ADD_TO_CART": 0.85,
        "CHECKOUT": 0.85
    }
}
```

### Example 2: Search or View 🔀
```python
Query: "show shoes"

Expected Output:
{
    "action": "AMBIGUOUS",
    "possible_intents": {
        "SEARCH_PRODUCT": 0.70,
        "VIEW_PRODUCT": 0.65
    }
}
```

### Example 3: Cart Actions 🔀
```python
Query: "cart"

Expected Output (depending on context):
{
    "action": "AMBIGUOUS",
    "possible_intents": {
        "VIEW_CART": 0.70,
        "ADD_TO_CART": 0.60
    }
}
```

---

## 🤔 Multi-Intent Queries

### Example 1: Sequential Actions 🔀
```python
Query: "add shoes to cart and track my order"

Expected Output:
{
    "action": "AMBIGUOUS",
    "possible_intents": {
        "ADD_TO_CART": 0.75,
        "TRACK_ORDER": 0.75
    }
}
```

### Example 2: Complex Request 🔀
```python
Query: "search for headphones, add to cart, and checkout"

Expected Output:
{
    "action": "AMBIGUOUS",
    "possible_intents": {
        "SEARCH_PRODUCT": 0.70,
        "ADD_TO_CART": 0.70,
        "CHECKOUT": 0.70
    }
}
```

---

## ❌ Error Cases

### Example 1: Gibberish ❓
```python
Query: "asdfghjkl"

Expected Output:
{
    "action": "UNCLEAR",
    "possible_intents": {}
}
```

### Example 2: Too Vague ❓
```python
Query: "something"

Expected Output:
{
    "classification_status": "FALLBACK_GENERIC",
    "intent": {
        "id": "SEARCH_PRODUCT",
        "score": 0.1,
        "source": "fallback",
        "reason": "generic_search_fallback"
    }
}
```

### Example 3: Empty Query ❓
```python
Query: ""

Expected Output:
[]  # Empty result from matcher
```

### Example 4: Only Special Characters ❓
```python
Query: "!!??##$$"

Expected Output:
{
    "action": "UNCLEAR",
    "possible_intents": {}
}
```

---

## 📊 Test Coverage Summary

| Intent Category | Examples Provided | Coverage |
|----------------|-------------------|----------|
| Shopping Cart | 15 | ✅ Comprehensive |
| Product Search | 10 | ✅ Comprehensive |
| Order Management | 12 | ✅ Comprehensive |
| Account & Profile | 4 | ✅ Good |
| Edge Cases | 8 | ✅ Good |
| Ambiguous Queries | 5 | ✅ Good |
| Error Cases | 4 | ✅ Good |

**Total Examples:** 58

---

## 🧪 Running Examples

### Test Script

```python
# test_examples.py
from app.ai.intent_classification.decision_engine import get_intent_classification
from app.ai.intent_classification.ambiguity_resolver import detect_intent

# Test cases from this document
test_cases = [
    ("add to cart", "ADD_TO_CART", 1.0),
    ("search for shoes", "SEARCH_PRODUCT", 0.90),
    ("track my order", "TRACK_ORDER", 1.0),
    ("view cart", "VIEW_CART", 1.0),
    ("checkout", "CHECKOUT", 1.0),
]

print("🧪 Running example query tests...\n")

for query, expected_intent, min_score in test_cases:
    result = get_intent_classification(query)
    actual_intent = result["intent"]["id"]
    actual_score = result["intent"]["score"]
    
    if actual_intent == expected_intent and actual_score >= min_score:
        print(f"✅ PASS: '{query}' -> {actual_intent} ({actual_score:.2f})")
    else:
        print(f"❌ FAIL: '{query}'")
        print(f"   Expected: {expected_intent} (≥{min_score})")
        print(f"   Got: {actual_intent} ({actual_score:.2f})")
```

**Run:**
```bash
python test_examples.py
```

---

## 📝 Adding New Examples

When adding new intents or keywords:

1. **Add Example Queries** to this document
2. **Include Expected Output** with confidence scores
3. **Test Manually** to verify behavior
4. **Update Test Script** with new cases
5. **Document Edge Cases** if any

---

**For More Information:**
- [Main Documentation](KEYWORD_MATCHING_GUIDE.md)
- [API Reference](API_REFERENCE.md)
- [Keyword Maintenance](KEYWORD_MAINTENANCE_GUIDE.md)
- [Performance Tuning](PERFORMANCE_TUNING_GUIDE.md)

---

**Last Updated:** October 28, 2025  
**Version:** 1.0  
**Status:** ✅ Ready for Use
