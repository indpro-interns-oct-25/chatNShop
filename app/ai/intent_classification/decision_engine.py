"""
Decision Engine
Core logic for hybrid intent classification combining keyword and embedding matchers.
Fully integrated with Config Manager for live rule switching and A/B testing.
"""

from typing import List, Dict, Any

# --- CONFIG MANAGER INTEGRATION ---
from app.core.config_manager import CONFIG_CACHE, ACTIVE_VARIANT
from app.ai.config import PRIORITY_THRESHOLD, WEIGHTS  # Static fallback configuration
from app.ai.intent_classification.keyword_matcher import KeywordMatcher
from app.ai.intent_classification.embedding_matcher import EmbeddingMatcher
from app.ai.intent_classification import confidence_threshold


class DecisionEngine:
    """
    Orchestrates the hybrid (keyword + embedding) classification process.
    Supports live A/B config variants and weighted blending logic.
    """

    def __init__(self):
        print("⚙️ Initializing DecisionEngine...")
        self.keyword_matcher = KeywordMatcher()
        self.embedding_matcher = EmbeddingMatcher()
        self._load_config()
        print(f"✅ DecisionEngine Initialized (Active Variant: {ACTIVE_VARIANT})")

    # -------------------------------------------------------------------------
    # CONFIGURATION MANAGEMENT
    # -------------------------------------------------------------------------
    def _load_config(self):
        """Load dynamic configuration from config manager or fallback to static."""
        try:
            rules = CONFIG_CACHE.get("rules", {}).get("rule_sets", {}).get(ACTIVE_VARIANT, {})
            self.use_keywords = rules.get("use_keywords", True)
            self.use_embedding = rules.get("use_embedding", True)
            self.priority_threshold = rules.get("priority_threshold", PRIORITY_THRESHOLD)
            self.kw_weight = rules.get("kw_weight", WEIGHTS["keyword"])
            self.emb_weight = rules.get("emb_weight", WEIGHTS["embedding"])
            print(f"📋 Loaded Config Variant '{ACTIVE_VARIANT}' → keywords={self.use_keywords}, embeddings={self.use_embedding}")
        except Exception as e:
            print(f"⚠️ Config load error ({e}) → using fallback defaults.")
            self.use_keywords = True
            self.use_embedding = True
            self.priority_threshold = PRIORITY_THRESHOLD
            self.kw_weight = WEIGHTS["keyword"]
            self.emb_weight = WEIGHTS["embedding"]

    # -------------------------------------------------------------------------
    # MAIN SEARCH LOGIC
    # -------------------------------------------------------------------------
    def search(self, query: str) -> Dict[str, Any]:
        """Main entry point — performs hybrid classification search."""
        self._load_config()  # Hot reload current variant config

        keyword_results, embedding_results = [], []

        # --- Keyword Matcher ---
        if self.use_keywords:
            keyword_results = self.keyword_matcher.search(query)
            if keyword_results and keyword_results[0]["score"] >= self.priority_threshold:
                print(f"✅ Priority Keyword Match: {keyword_results[0]['id']}")
                return self._build_response("CONFIDENT_KEYWORD", keyword_results[0])

        # --- Embedding Matcher ---
        if self.use_embedding:
            embedding_results = self.embedding_matcher.search(query)

        # --- Blending Results ---
        if self.use_keywords and self.use_embedding:
            blended_results = self._blend_results(keyword_results, embedding_results)
        else:
            blended_results = keyword_results or embedding_results

        if not blended_results:
            return self._fallback_no_match(query, keyword_results, embedding_results)

        # --- Confidence Evaluation ---
        is_confident, reason = confidence_threshold.is_confident(blended_results)
        top_result = blended_results[0]

        if is_confident:
            print(f"✅ Confident result → {top_result['intent']} | Reason: {reason}")
            return self._build_response(reason, top_result)
        else:
            print(f"⚠️ Low Confidence ({reason}), triggering fallback...")
            return self._fallback_low_confidence(blended_results, reason)

    # -------------------------------------------------------------------------
    # BLENDING LOGIC
    # -------------------------------------------------------------------------
    def _blend_results(self, kw_results: List[Dict], emb_results: List[Dict]) -> List[Dict]:
        """Blend keyword and embedding scores using weighted logic."""
        if not kw_results and not emb_results:
            return []
        if not kw_results:
            return emb_results
        if not emb_results:
            return kw_results

        intent_scores = {}

        # Collect keyword results
        for r in kw_results:
            intent_id = r.get("id", r.get("intent"))
            intent_scores[intent_id] = {
                "keyword_score": r.get("score", 0.0),
                "embedding_score": 0.0,
                "keyword_result": r,
                "embedding_result": None,
            }

        # Merge embedding results
        for r in emb_results:
            intent_id = r.get("id", r.get("intent"))
            if intent_id in intent_scores:
                intent_scores[intent_id]["embedding_score"] = r.get("score", 0.0)
                intent_scores[intent_id]["embedding_result"] = r
            else:
                intent_scores[intent_id] = {
                    "keyword_score": 0.0,
                    "embedding_score": r.get("score", 0.0),
                    "keyword_result": None,
                    "embedding_result": r,
                }

        # Weighted score computation
        blended_results = []
        for intent_id, s in intent_scores.items():
            blended_score = (s["keyword_score"] * self.kw_weight) + (s["embedding_score"] * self.emb_weight)
            base = s["keyword_result"] if s["keyword_score"] >= s["embedding_score"] else s["embedding_result"]
            if not base:
                continue

            result = base.copy()
            result.update({
                "score": blended_score,
                "source": "blended",
                "keyword_score": s["keyword_score"],
                "embedding_score": s["embedding_score"],
            })
            blended_results.append(result)

        blended_results.sort(key=lambda x: x["score"], reverse=True)
        return blended_results

    # -------------------------------------------------------------------------
    # FALLBACK LOGIC
    # -------------------------------------------------------------------------
    def _fallback_no_match(self, query, kw, emb):
        """Handle completely unmatched queries."""
        print(f"⚠️ No confident match found for query → '{query}'")

        if emb:
            emb_fallback = [r for r in emb if r["score"] >= 0.3]
            if emb_fallback:
                print("✅ Fallback embedding match selected.")
                return self._build_response("FALLBACK_EMBEDDING", emb_fallback[0])

        if kw:
            kw_fallback = [r for r in kw if r["score"] >= 0.3]
            if kw_fallback:
                print("✅ Fallback keyword match selected.")
                return self._build_response("FALLBACK_KEYWORD", kw_fallback[0])

        print("⚠️ Defaulting to generic search intent.")
        return self._build_response("FALLBACK_GENERIC", {
            "id": "SEARCH_PRODUCT",
            "intent": "SEARCH_PRODUCT",
            "score": 0.1,
            "source": "fallback",
            "reason": "generic_search_fallback",
        })

    def _fallback_low_confidence(self, results, reason):
        """Fallback handler for low-confidence results."""
        if results and results[0]["score"] >= 0.1:
            print("✅ Using top result as fallback.")
            return self._build_response(f"FALLBACK_{reason}", results[0])

        print("⚠️ No suitable fallback, returning generic search intent.")
        return self._build_response("FALLBACK_GENERIC", {
            "id": "SEARCH_PRODUCT",
            "intent": "SEARCH_PRODUCT",
            "score": 0.1,
            "source": "fallback",
            "reason": "generic_search_fallback",
        })

    # -------------------------------------------------------------------------
    # RESPONSE WRAPPER
    # -------------------------------------------------------------------------
    def _build_response(self, status: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Create a consistent API response format."""
        return {
            "status": status,
            "intent": intent,
            "config_variant": ACTIVE_VARIANT,
        }


# -------------------------------------------------------------------------
# GLOBAL ENTRYPOINT
# -------------------------------------------------------------------------
_decision_engine = None


def get_intent_classification(query: str) -> Dict[str, Any]:
    """Global interface for intent classification API."""
    global _decision_engine
    if _decision_engine is None:
        _decision_engine = DecisionEngine()
    return _decision_engine.search(query)
