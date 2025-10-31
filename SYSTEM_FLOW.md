# System Flow: End-to-End Architecture and Execution

## 🎯 Purpose
A single, consolidated reference for how the intent classification system works from request to response, including endpoints, orchestration, hybrid matching, confidence evaluation, LLM fallback, and data/decision flows.

---

## 🚪 API Endpoints

- Primary endpoint (recommended):
  - Path: `/classify`
  - File: `app/main.py` → `classify_intent()`
  - Flow: Rule-based → Hybrid → Confidence → LLM fallback (if needed) → Generic fallback

- Optional debug endpoint (if enabled):
  - Path: `/api/v1/llm-intent/classify`
  - File: `app/api/v1/intent.py` → `classify_intent()`
  - Flow: Direct LLM classification (bypasses rule-based flow). Keep disabled in prod unless needed for debugging.

---

## 🧠 High-Level Flow

```
POST /classify {"text": "add to cart"}
    └─> DecisionEngine.search(query)
        ├─> Load config (hot-reload, A/B variant)
        ├─> KeywordMatcher.search(query)
        │    └─> Priority rule: if score >= 0.85 → return immediately
        ├─> EmbeddingMatcher.search(query)  # if not short-circuited
        ├─> HybridClassifier.blend(keyword, embedding)
        ├─> confidence_threshold.is_confident(results)
        │    ├─> ✅ Confident → return
        │    └─> ❌ Not confident → LLM fallback (if available)
        ├─> LLM fallback via RequestHandler (optional)
        └─> Generic fallback (SEARCH_PRODUCT) if nothing suitable
```

---

## 🔩 Component Responsibilities

- `app/main.py` (API)
  - Receives request, calls `get_intent_classification(text)`, formats response

- `decision_engine.py` (Orchestrator)
  - Coordinates keyword + embedding
  - Applies priority rule, calls `HybridClassifier`
  - Evaluates confidence and triggers LLM fallback
  - Fallbacks: thresholds↓ and generic `SEARCH_PRODUCT`

- `keyword_matcher.py` (Rules)
  - Normalize, segment, match keywords/regex/partials
  - Scoring and sorting; returns `[{id, score, source, matched_text}]`

- `embedding_matcher.py` (Semantic)
  - Lazy-load SentenceTransformer, encode query
  - Cosine similarity vs reference intent embeddings

- `hybrid_classifier.py` (Blend)
  - Weighted blend: `kw_weight * kw_score + emb_weight * emb_score`
  - Conflict resolution; sort by blended score

- `confidence_threshold.py` (Confidence)
  - Absolute threshold and top-2 gap checks

- `app/ai/llm_intent/request_handler.py` (LLM Fallback)
  - Trigger logic, optional OpenAI call, parse normalized response

- `intents_modular/` (Intent taxonomy)
  - Action codes, categories, definitions, examples, utilities

---

## ⚖️ Decision Points

1) Priority Short-Circuit
- If top keyword score ≥ `priority_threshold` (e.g., 0.85) → return immediately

2) Blending Strategy
- Both enabled → blend results
- Only keywords/embedding → pass-through

3) Confidence Evaluation
- Top score ≥ absolute min (e.g., 0.3)
- Score gap (top - second) ≥ min diff (e.g., 0.05)

4) LLM Fallback (optional)
- Triggered when not confident/ambiguous and LLM available

5) Generic Fallback
- If no suitable results → return `SEARCH_PRODUCT`

---

## 🧮 Data Shapes

- Keyword/Embedding result item:
```json
{
  "id": "ADD_TO_CART",
  "score": 0.9,
  "source": "keyword", // or "embedding"
  "matched_text": "add to cart" // keyword only
}
```

- Blended result item:
```json
{
  "id": "ADD_TO_CART",
  "score": 0.888,         
  "source": "blended",
  "keyword_score": 0.9,
  "embedding_score": 0.87
}
```

- DecisionEngine response:
```json
{
  "status": "CONFIDENT_KEYWORD" | "BLENDED_TOP_CONFIDENT" | "LLM_FALLBACK" | "FALLBACK_GENERIC",
  "intent": { /* top result item */ },
  "config_variant": "A" | "B"
}
```

- API response (`/classify`):
```json
{
  "action_code": "ADD_TO_CART",
  "confidence_score": 0.92,
  "matched_keywords": ["add to cart"],
  "original_text": "add to cart",
  "status": "CONFIDENT_KEYWORD",
  "intent": { /* top result item */ }
}
```

---

## 🧭 Detailed Orchestration (Key Lines)

- `app/main.py`
  - `get_intent_classification(user_input.text)` → routes to DecisionEngine

- `decision_engine.py`
  - Loads config; updates `HybridClassifier` weights
  - Keyword first → priority short-circuit if high
  - Embedding next (lazy init)
  - Blend via `hybrid_classifier.blend(kw, emb)`
  - Confidence evaluation → LLM fallback if needed
  - Fallbacks: embedding↓, keyword↓, generic intent

- `hybrid_classifier.py`
  - `blend()` merges by intent, computes weighted score, sorts

- `intents_modular/taxonomy.py`
  - Provides taxonomy utilities and statistics (fixed initialization and action code handling)

---

## 🧪 Testing

- Unit tests:
  - `tests/intent_classification_tests/unit/test_hybrid_classifier.py`
  - `tests/intent_classification_tests/unit/test_hybrid_decision.py`

- Quick commands:
```bash
# venv
source venv/bin/activate

# Unit tests
pytest tests/intent_classification_tests/unit/test_hybrid_classifier.py -v
pytest tests/intent_classification_tests/unit/test_hybrid_decision.py -v

# All tests
pytest tests/intent_classification_tests/ -v
```

---

## ⚙️ Configuration & A/B

- Dynamic config via `config_manager`
- Hot-reload settings (weights, thresholds, switches)
- `HybridClassifier.update_weights(kw, emb)` called as config changes

---

## ⚡ Performance Notes

- Keyword: typically < 50ms
- Embedding: 50–100ms (lazy-loaded model)
- Hybrid blend: < 1ms
- Priority rule short-circuit saves ~80ms by skipping embeddings
- LLM fallback: 200–500ms (only when needed)

---

## 🧱 Development Pointers

- Add/modify intents: `intents_modular/definitions/*` and `enums.py`
- Keyword dictionaries: `keywords/*.json`
- Tweak thresholds/weights: config (hot-reload) or `app/ai/config.py`
- Change decision rules: `decision_engine.py` → `search()`
- Change blending: `hybrid_classifier.py` → `blend()`

---

## ✅ Summary
- Use `/classify` as the single public endpoint.
- The DecisionEngine coordinates keyword + embedding, blends, checks confidence, and optionally triggers the LLM as a final fallback.
- The taxonomy and action code handling are fixed and robust to both Enum-like and string-based definitions.

## 📈 Visual Flow Diagrams

Flow 1: End-to-End Request → Response

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER REQUEST                                   │
│  POST /classify {"text": "add to cart"}                                │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 1: API ENTRY POINT                                                │
│  File: app/main.py                                                      │
│  Function: classify_intent(user_input)                                  │
│  • Validates input (Pydantic)                                           │
│  • Calls get_intent_classification(text)                                 │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 2: DECISION ENGINE                                                │
│  File: decision_engine.py                                               │
│  Method: DecisionEngine.search(query)                                   │
│  • Load config (hot-reload/A-B)                                         │
│  • KeywordMatcher.search(query)                                         │
│  • Priority rule (≥ 0.85)? → return                                     │
│  • EmbeddingMatcher.search(query)                                       │
│  • HybridClassifier.blend(kw, emb)                                      │
│  • confidence_threshold.is_confident(...)                                │
│    ├─> ✅ Confident → return                                            │
│    └─> ❌ Not confident → LLM fallback (if available)                    │
│  • Fallbacks: thresholds↓, generic SEARCH_PRODUCT                       │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 3: API RESPONSE                                                   │
│  File: app/main.py                                                      │
│  • Shape DecisionEngine result → ClassificationOutput                    │
│  • Return JSON (action_code, confidence_score, matched_keywords, ...)   │
└─────────────────────────────────────────────────────────────────────────┘
```

Flow 2: Component Connection Map

```
┌─────────────────────────────────────────────────────────────────┐
│                          API LAYER                               │
│  app/main.py                                                     │
│    └─ POST /classify → get_intent_classification(text)           │
└───────────────┬─────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATION LAYER                          │
│  decision_engine.py                                              │
│    └─ DecisionEngine.search                                      │
│       ├─ KeywordMatcher.search                                   │
│       ├─ EmbeddingMatcher.search (lazy)                          │
│       ├─ HybridClassifier.blend                                  │
│       ├─ confidence_threshold.is_confident                        │
│       ├─ LLM fallback (optional)                                 │
│       └─ Fallbacks (thresholds↓, SEARCH_PRODUCT)                 │
└───────────────┬───────────────────────┬──────────────────────────┘
                │                       │
                ▼                       ▼
      ┌──────────────────┐     ┌──────────────────┐
      │ KeywordMatcher   │     │ EmbeddingMatcher │
      │ keyword_matcher  │     │ embedding_matcher│
      │  • normalize     │     │  • encode        │
      │  • match/score   │     │  • cosine sim    │
      └─────────┬────────┘     └─────────┬────────┘
                │                        │
                └────────────┬───────────┘
                             ▼
                   ┌──────────────────────┐
                   │ HybridClassifier     │
                   │ hybrid_classifier    │
                   │  • weighted blend    │
                   │  • conflict resolve  │
                   └──────────┬───────────┘
                              ▼
                   ┌──────────────────────┐
                   │ Confidence Threshold │
                   │ confidence_threshold │
                   │  • abs + gap checks │
                   └──────────┬───────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
             ┌──────────────┐   ┌─────────────────┐
             │  Return      │   │  LLM Fallback   │
             │  result      │   │  request_handler│
             └──────────────┘   └─────────────────┘
```

Flow 3: Decision Tree (Condensed)

```
Query
  ├─ Keyword score ≥ 0.85? → ✅ RETURN (CONFIDENT_KEYWORD)
  └─ Else
     ├─ Compute embedding
     ├─ Blend keyword + embedding
     ├─ Confident? → ✅ RETURN (BLENDED_TOP_CONFIDENT)
     └─ Not confident
        ├─ LLM available? → Call LLM → RETURN (LLM_FALLBACK)
        └─ Else → RETURN (FALLBACK_GENERIC: SEARCH_PRODUCT)
```
