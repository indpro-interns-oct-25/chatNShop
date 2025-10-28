# Keyword Maintenance Guide

**Task:** CNS-16 - Keyword Maintenance Deliverable  
**Date:** October 28, 2025  
**Version:** 1.0

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Keyword File Structure](#keyword-file-structure)
3. [Adding New Keywords](#adding-new-keywords)
4. [Adding New Intents](#adding-new-intents)
5. [Modifying Existing Keywords](#modifying-existing-keywords)
6. [Testing Keywords](#testing-keywords)
7. [Best Practices](#best-practices)
8. [Common Pitfalls](#common-pitfalls)
9. [Validation Checklist](#validation-checklist)

---

## 🎯 Overview

This guide covers everything you need to know about maintaining keyword dictionaries for the Rule-Based Keyword Matching System. Keywords are stored in JSON files and directly impact intent classification accuracy.

**Key Files:**
- `app/ai/intent_classification/keywords/cart_keywords.json`
- `app/ai/intent_classification/keywords/product_keywords.json`
- `app/ai/intent_classification/keywords/search_keywords.json`

**Related Components:**
- CNS-7: Intent Taxonomy (defines valid action codes)
- CNS-8: Keyword Dictionaries (these JSON files)
- `keywords/loader.py`: Loads and validates keyword files

---

## 📁 Keyword File Structure

### Basic JSON Structure

```json
{
    "ACTION_CODE": {
        "action": "ACTION_CODE",
        "priority": 1,
        "keywords": [
            "keyword phrase 1",
            "keyword phrase 2",
            "\\bregex\\b pattern",
            "another keyword"
        ]
    },
    "ANOTHER_ACTION": {
        "action": "ANOTHER_ACTION",
        "priority": 2,
        "keywords": [...]
    }
}
```

### Field Descriptions

#### `ACTION_CODE` (Object Key)
- **Type:** String
- **Purpose:** Unique identifier for the intent
- **Rules:** 
  - Must match CNS-7 taxonomy action codes
  - UPPERCASE with underscores (e.g., `ADD_TO_CART`)
  - Should be identical to the `action` field value

#### `action` (Field)
- **Type:** String
- **Purpose:** Action code to return when matched
- **Rules:** Must match the object key exactly

#### `priority` (Field)
- **Type:** Integer (1-10)
- **Purpose:** Determines precedence when multiple intents match
- **Rules:**
  - Lower number = higher priority (1 is highest)
  - Use 1 for critical actions (e.g., `ADD_TO_CART`, `CHECKOUT`)
  - Use 2-3 for common actions (e.g., `SEARCH_PRODUCT`)
  - Use 4-5 for secondary actions (e.g., `VIEW_HISTORY`)

#### `keywords` (Field)
- **Type:** Array of strings
- **Purpose:** Patterns to match against user queries
- **Rules:**
  - Can be exact phrases or regex patterns
  - Case-insensitive matching
  - Regex patterns must be valid Python regex
  - Recommend 10-30 keywords per intent for good coverage

---

## ➕ Adding New Keywords

### Step-by-Step Process

#### Step 1: Identify the Intent
Determine which action code the keywords belong to. Check CNS-7 taxonomy:
```python
# List all available action codes
from app.ai.intent_classification.intents_modular.taxonomy import ACTION_CODE_MAP
print(ACTION_CODE_MAP.keys())
```

#### Step 2: Choose the Right JSON File
- **cart_keywords.json**: Shopping cart actions (add, remove, view cart)
- **product_keywords.json**: Product-related actions (view, details, compare)
- **search_keywords.json**: Search and discovery actions

#### Step 3: Add Keywords to Array
```json
{
    "ADD_TO_CART": {
        "action": "ADD_TO_CART",
        "priority": 1,
        "keywords": [
            "add to cart",
            "add to bag",
            "put in cart",
            "add item",
            // NEW KEYWORDS BELOW
            "add this",
            "i want this",
            "buy this",
            "\\bcart\\b.*\\badd\\b"
        ]
    }
}
```

#### Step 4: Validate JSON Syntax
```bash
# Use Python to validate
python -m json.tool app/ai/intent_classification/keywords/cart_keywords.json

# Or use online validator: jsonlint.com
```

#### Step 5: Test the Keywords
```python
from app.ai.intent_classification.keyword_matcher import KeywordMatcher

matcher = KeywordMatcher()
results = matcher.search("i want this in my cart")
print(results)
# Should return ADD_TO_CART with good confidence
```

### Example: Adding "Browse" Keywords

**Before:**
```json
{
    "SEARCH_PRODUCT": {
        "action": "SEARCH_PRODUCT",
        "priority": 2,
        "keywords": [
            "search",
            "find",
            "look for"
        ]
    }
}
```

**After:**
```json
{
    "SEARCH_PRODUCT": {
        "action": "SEARCH_PRODUCT",
        "priority": 2,
        "keywords": [
            "search",
            "find",
            "look for",
            "browse",
            "show me",
            "looking for",
            "i need"
        ]
    }
}
```

---

## 🆕 Adding New Intents

### Prerequisites
1. Intent must exist in CNS-7 taxonomy
2. Action code must be defined in `ACTION_CODE_MAP`
3. Choose appropriate JSON file

### Step-by-Step Process

#### Step 1: Verify Intent in CNS-7
```python
from app.ai.intent_classification.intents_modular.taxonomy import ACTION_CODE_MAP

# Check if intent exists
if "SAVE_FOR_LATER" in ACTION_CODE_MAP:
    print("✅ Intent exists in taxonomy")
else:
    print("❌ Add to taxonomy first")
```

#### Step 2: Determine Priority Level
- Priority 1: Critical transaction actions
- Priority 2: Common user actions
- Priority 3-4: Secondary features
- Priority 5+: Rare or edge case actions

#### Step 3: Brainstorm Keywords
Think about:
- How users naturally phrase this intent
- Variations and synonyms
- Common typos or abbreviations
- Formal and informal language

#### Step 4: Add to Appropriate JSON File
```json
{
    "EXISTING_INTENT": {
        ...
    },
    "SAVE_FOR_LATER": {
        "action": "SAVE_FOR_LATER",
        "priority": 3,
        "keywords": [
            "save for later",
            "save this",
            "save item",
            "add to wishlist",
            "wishlist",
            "save to favorites",
            "bookmark this",
            "\\bsave\\b",
            "\\bwishlist\\b"
        ]
    }
}
```

#### Step 5: Reload and Test
```bash
# Restart the application to reload keywords
# Or re-initialize the matcher

python -c "
from app.ai.intent_classification.keyword_matcher import KeywordMatcher
matcher = KeywordMatcher()
results = matcher.search('save for later')
print(results)
"
```

### Complete Example: Adding "COMPARE_PRODUCTS"

**1. Verify in CNS-7:**
```python
# Assume COMPARE_PRODUCTS exists in ACTION_CODE_MAP
```

**2. Add to product_keywords.json:**
```json
{
    "VIEW_PRODUCT": {
        "action": "VIEW_PRODUCT",
        "priority": 2,
        "keywords": ["view product", "show product", "product details"]
    },
    "COMPARE_PRODUCTS": {
        "action": "COMPARE_PRODUCTS",
        "priority": 3,
        "keywords": [
            "compare",
            "compare products",
            "compare items",
            "comparison",
            "compare these",
            "difference between",
            "which is better",
            "\\bcompare\\b.*\\bproduct",
            "product comparison",
            "vs",
            "versus"
        ]
    }
}
```

**3. Test:**
```python
matcher = KeywordMatcher()

# Test case 1
result = matcher.search("compare these two products")
assert result[0]["id"] == "COMPARE_PRODUCTS"

# Test case 2
result = matcher.search("which is better, product A vs B")
assert result[0]["id"] == "COMPARE_PRODUCTS"
```

---

## ✏️ Modifying Existing Keywords

### When to Modify
- User queries not matching as expected
- Too many false positives
- Priority conflicts between intents
- Regex patterns not working correctly

### Safe Modification Process

#### 1. Document Current Behavior
```python
# Before modification
test_queries = [
    "add to cart",
    "put in cart",
    "add item"
]

for query in test_queries:
    result = matcher.search(query)
    print(f"{query} -> {result[0]['id']} (score: {result[0]['score']})")
```

#### 2. Make Changes
```json
// Before
{
    "ADD_TO_CART": {
        "keywords": ["add to cart", "add to bag"]
    }
}

// After - Adding more variations
{
    "ADD_TO_CART": {
        "keywords": [
            "add to cart",
            "add to bag",
            "put in cart",
            "add this to cart",
            "cart add"
        ]
    }
}
```

#### 3. Validate Changes
```python
# After modification - test same queries
for query in test_queries:
    result = matcher.search(query)
    print(f"{query} -> {result[0]['id']} (score: {result[0]['score']})")
```

#### 4. Test Edge Cases
```python
# Test potential conflicts
ambiguous_queries = [
    "add and search",  # Could match multiple intents
    "cart",            # Too short
    "add"              # Too vague
]

for query in ambiguous_queries:
    results = matcher.search(query, top_n=3)
    print(f"\n{query}:")
    for r in results:
        print(f"  {r['id']}: {r['score']}")
```

### Changing Priority

**Scenario:** "VIEW_CART" is matching before "ADD_TO_CART" for query "add to my cart"

**Solution:**
```json
// Before
{
    "ADD_TO_CART": {"priority": 2, ...},
    "VIEW_CART": {"priority": 2, ...}
}

// After - Give ADD_TO_CART higher priority
{
    "ADD_TO_CART": {"priority": 1, ...},
    "VIEW_CART": {"priority": 2, ...}
}
```

---

## 🧪 Testing Keywords

### Manual Testing Script

```python
# test_keywords.py
from app.ai.intent_classification.keyword_matcher import KeywordMatcher

matcher = KeywordMatcher()

# Define test cases
test_cases = [
    ("add to cart", "ADD_TO_CART", 0.8),
    ("search for shoes", "SEARCH_PRODUCT", 0.7),
    ("track my order", "TRACK_ORDER", 0.9),
    ("i want to add this item to my shopping bag", "ADD_TO_CART", 0.7),
]

print("Running keyword tests...\n")
passed = 0
failed = 0

for query, expected_intent, min_score in test_cases:
    results = matcher.search(query)
    
    if results and results[0]["id"] == expected_intent and results[0]["score"] >= min_score:
        print(f"✅ PASS: '{query}' -> {expected_intent} (score: {results[0]['score']:.2f})")
        passed += 1
    else:
        actual = results[0] if results else None
        print(f"❌ FAIL: '{query}'")
        print(f"   Expected: {expected_intent} (score >= {min_score})")
        print(f"   Got: {actual['id'] if actual else 'No match'} (score: {actual['score'] if actual else 0:.2f})")
        failed += 1

print(f"\n{passed} passed, {failed} failed")
```

### Automated Testing

Create unit tests for keyword matching:

```python
# tests/test_keywords.py
import pytest
from app.ai.intent_classification.keyword_matcher import KeywordMatcher

@pytest.fixture
def matcher():
    return KeywordMatcher()

def test_add_to_cart_exact(matcher):
    results = matcher.search("add to cart")
    assert len(results) > 0
    assert results[0]["id"] == "ADD_TO_CART"
    assert results[0]["score"] >= 0.9

def test_search_product_partial(matcher):
    results = matcher.search("search for red shoes")
    assert len(results) > 0
    assert results[0]["id"] == "SEARCH_PRODUCT"
    assert results[0]["score"] >= 0.6

def test_no_match(matcher):
    results = matcher.search("xyz123abc")
    assert len(results) == 0

# Run with: pytest tests/test_keywords.py
```

### Performance Testing

```python
# test_performance.py
import time
from app.ai.intent_classification.keyword_matcher import KeywordMatcher

matcher = KeywordMatcher()
queries = ["add to cart"] * 1000

start = time.time()
for query in queries:
    matcher.search(query)
end = time.time()

avg_latency = (end - start) / len(queries) * 1000  # ms
print(f"Average latency: {avg_latency:.2f}ms")
print(f"Throughput: {len(queries) / (end - start):.0f} queries/sec")
```

---

## ✅ Best Practices

### 1. Keyword Quality
- **Use natural language**: How users actually speak
- **Include variations**: Synonyms, abbreviations, typos
- **Be specific**: Avoid overly generic terms like "item", "thing"
- **Test thoroughly**: Use real user queries

### 2. Quantity Guidelines
- **Minimum**: 5-10 keywords per intent
- **Optimal**: 15-25 keywords per intent
- **Maximum**: 30-40 keywords (beyond this, diminishing returns)

### 3. Priority Management
```
Priority 1: Critical actions (checkout, payment, add_to_cart)
Priority 2: Common actions (search, view_product, view_cart)
Priority 3: Secondary actions (wishlist, compare, reviews)
Priority 4+: Rare actions (print, share, help)
```

### 4. Regex Patterns
- Use `\\b` for word boundaries: `\\bcart\\b`
- Use `.*` for flexible matching: `\\btrack\\b.*\\border\\b`
- Test regex on https://regex101.com before adding
- Keep patterns simple - complex regex impacts performance

### 5. File Organization
- Group related intents in same file
- Keep files under 500 lines for maintainability
- Use consistent formatting (2-space indentation)
- Add comments for complex patterns

### 6. Version Control
- Commit keyword changes separately from code changes
- Use descriptive commit messages: "Add 'buy now' keywords to ADD_TO_CART"
- Test before pushing to production

---

## ⚠️ Common Pitfalls

### 1. Keyword Overlap
**Problem:** Multiple intents match the same query

```json
// BAD - "add" appears in both
{
    "ADD_TO_CART": {"keywords": ["add", "add to cart"]},
    "ADD_TO_WISHLIST": {"keywords": ["add", "add to wishlist"]}
}

// GOOD - More specific keywords
{
    "ADD_TO_CART": {"keywords": ["add to cart", "put in cart", "cart add"]},
    "ADD_TO_WISHLIST": {"keywords": ["add to wishlist", "save for later", "wishlist add"]}
}
```

### 2. Overly Generic Keywords
**Problem:** Matches too many unrelated queries

```json
// BAD
{
    "SEARCH_PRODUCT": {"keywords": ["product", "item", "show"]}
}

// GOOD
{
    "SEARCH_PRODUCT": {"keywords": ["search product", "find product", "show me products"]}
}
```

### 3. Invalid Regex
**Problem:** Regex syntax errors cause matcher to skip pattern

```json
// BAD - Unescaped special characters
{
    "TRACK_ORDER": {"keywords": ["track(order)"]}  // Invalid regex
}

// GOOD - Properly escaped
{
    "TRACK_ORDER": {"keywords": ["\\btrack\\b.*\\border\\b"]}
}
```

### 4. Priority Conflicts
**Problem:** Lower priority intent wins due to better match

```json
// PROBLEM: If both match, which wins?
{
    "ADD_TO_CART": {"priority": 2, "keywords": ["cart"]},
    "VIEW_CART": {"priority": 1, "keywords": ["view cart", "show cart"]}
}

// Query: "cart" -> VIEW_CART wins (priority 1) even though ADD_TO_CART is more generic
```

**Solution:** Use priority 1 for most important actions, ensure higher-priority intents have more specific keywords.

### 5. Case Sensitivity Assumption
**Problem:** Assuming keywords need specific casing

```json
// UNNECESSARY - System is case-insensitive
{
    "ADD_TO_CART": {"keywords": ["Add To Cart", "ADD TO CART", "add to cart"]}
}

// SUFFICIENT
{
    "ADD_TO_CART": {"keywords": ["add to cart"]}
}
```

### 6. Missing Action Code Sync
**Problem:** Action code doesn't match CNS-7 taxonomy

```json
// BAD - Typo in action code
{
    "ADD_TO_CART": {
        "action": "ADD_CART",  // Should be ADD_TO_CART
        "keywords": [...]
    }
}
```

**Result:** Intent won't be recognized by downstream systems.

---

## 📋 Validation Checklist

Before committing keyword changes, verify:

- [ ] JSON syntax is valid (run through validator)
- [ ] Action codes match CNS-7 taxonomy exactly
- [ ] Object key matches `action` field value
- [ ] Priority values are 1-10
- [ ] Keywords array has at least 5 entries
- [ ] No duplicate keywords within same intent
- [ ] Regex patterns tested and valid
- [ ] Tested with sample queries (manual or automated)
- [ ] No unintended keyword overlaps with other intents
- [ ] File encoding is UTF-8
- [ ] Proper indentation and formatting
- [ ] Committed with descriptive message

### Validation Commands

```bash
# 1. Validate JSON syntax
python -m json.tool app/ai/intent_classification/keywords/cart_keywords.json > /dev/null && echo "✅ Valid JSON"

# 2. Check file encoding
file -i app/ai/intent_classification/keywords/cart_keywords.json
# Should show: charset=utf-8

# 3. Count keywords per intent
python -c "
import json
with open('app/ai/intent_classification/keywords/cart_keywords.json') as f:
    data = json.load(f)
    for intent, details in data.items():
        print(f'{intent}: {len(details[\"keywords\"])} keywords')
"

# 4. Run test suite
pytest tests/test_keywords.py -v

# 5. Check for duplicates
python -c "
import json
with open('app/ai/intent_classification/keywords/cart_keywords.json') as f:
    data = json.load(f)
    all_keywords = []
    for intent, details in data.items():
        all_keywords.extend(details['keywords'])
    duplicates = [k for k in all_keywords if all_keywords.count(k) > 1]
    if duplicates:
        print(f'⚠️  Duplicates found: {set(duplicates)}')
    else:
        print('✅ No duplicates')
"
```

---

## 🔄 Maintenance Workflow

### Regular Maintenance Tasks

**Weekly:**
- Review ambiguous query logs (`ambiguous_log.json`)
- Identify common patterns that should be added
- Update keywords based on user feedback

**Monthly:**
- Audit all keyword files for quality
- Remove obsolete or redundant keywords
- Rebalance priorities based on usage patterns
- Run full test suite

**Quarterly:**
- Major keyword cleanup and reorganization
- Performance benchmarking
- Sync with CNS-7 taxonomy updates

### Workflow Diagram

```
1. Identify Issue
   ↓
2. Locate Appropriate JSON File
   ↓
3. Make Changes (add/modify/delete keywords)
   ↓
4. Validate JSON Syntax
   ↓
5. Test Locally
   ↓
6. Run Automated Tests
   ↓
7. Commit with Descriptive Message
   ↓
8. Deploy & Monitor
   ↓
9. Collect Feedback
   ↓
10. Return to Step 1
```

---

## 📞 Support & Resources

**Documentation:**
- [Main Guide](KEYWORD_MATCHING_GUIDE.md)
- [API Reference](API_REFERENCE.md)
- [Performance Tuning](PERFORMANCE_TUNING_GUIDE.md)

**Tools:**
- JSON Validator: https://jsonlint.com
- Regex Tester: https://regex101.com
- Python JSON module: `python -m json.tool`

**Contact:**
For questions about keyword maintenance, reach out to the chatNShop AI team.

---

**Last Updated:** October 28, 2025  
**Version:** 1.0  
**Status:** ✅ Ready for Use
