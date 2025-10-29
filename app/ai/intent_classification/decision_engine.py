"""
Decision Engine
This file contains the main logic for the intent classification.
Now integrated with config manager for dynamic configuration and A/B testing.
Also integrated with Qdrant for storing classified query embeddings.
"""
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

# --- CONFIG MANAGER INTEGRATION ---
from app.core.config_manager import CONFIG_CACHE, ACTIVE_VARIANT, switch_variant
from app.ai.config import PRIORITY_THRESHOLD, WEIGHTS  # Fallback config
from app.ai.intent_classification.keyword_matcher import KeywordMatcher
from app.ai.intent_classification.embedding_matcher import EmbeddingMatcher
from app.ai.intent_classification import confidence_threshold

# --- QDRANT INTEGRATION ---
from app.ai.llm_intent.qdrant_cache import store_vector


class DecisionEngine:
    """Orchestrates the hybrid search process with Qdrant caching."""

    def __init__(self):
        """Initializes the Decision Engine and its constituent matchers."""
        print("Initializing DecisionEngine...")
        self.keyword_matcher = KeywordMatcher()
        self.embedding_matcher = EmbeddingMatcher()
        self._load_config_from_manager()
        print(f"✅ DecisionEngine Initialized: Settings loaded from config manager (variant: {ACTIVE_VARIANT})")

    # ------------------------------------------------------------------
    def _load_config_from_manager(self):
        """Load configuration from config manager with fallback to static config."""
        try:
            rules = CONFIG_CACHE.get('rules', {}).get('rule_sets', {}).get(ACTIVE_VARIANT, {})
            if rules:
                self.use_embedding = rules.get('use_embedding', True)
                self.use_keywords = rules.get('use_keywords', True)
                print(f"📋 Using config manager rules for variant {ACTIVE_VARIANT}: embedding={self.use_embedding}, keywords={self.use_keywords}")
            else:
                self.use_embedding = True
                self.use_keywords = True
                self.priority_threshold = PRIORITY_THRESHOLD
                self.kw_weight = WEIGHTS["keyword"]
                self.emb_weight = WEIGHTS["embedding"]
                print("📋 Using fallback static config")
        except Exception as e:
            print(f"⚠️ Config manager error, using fallback: {e}")
            self.use_embedding = True
            self.use_keywords = True
            self.priority_threshold = PRIORITY_THRESHOLD
            self.kw_weight = WEIGHTS["keyword"]
            self.emb_weight = WEIGHTS["embedding"]

    # ------------------------------------------------------------------
    def search(self, query: str) -> Dict[str, Any]:
        """Executes the full hybrid search flow and evaluates confidence."""
        self._load_config_from_manager()

        keyword_results = []
        embedding_results = []

        # Keyword matching
        if self.use_keywords:
            keyword_results = self.keyword_matcher.search(query)
            if keyword_results and keyword_results[0]['score'] >= getattr(self, 'priority_threshold', PRIORITY_THRESHOLD):
                print(f"✅ Priority rule triggered. Returning high-confidence keyword match: {keyword_results[0]['id']}")
                result = {
                    "status": "CONFIDENT_KEYWORD",
                    "intent": keyword_results[0],
                    "config_variant": ACTIVE_VARIANT
                }
                self._store_in_qdrant(query, result)
                return result

        # Embedding matching
        if self.use_embedding:
            embedding_results = self.embedding_matcher.search(query)

        # Combine results
        if self.use_keywords and self.use_embedding:
            blended_results = self._blend_results(keyword_results, embedding_results)
        elif self.use_keywords and keyword_results:
            blended_results = keyword_results
        elif self.use_embedding and embedding_results:
            blended_results = embedding_results
        else:
            blended_results = []

        # Fallback if no matches
        if not blended_results:
            print(f"⚠ No match found for query: '{query}', trying fallback...")
            result = self._handle_no_match(query, keyword_results, embedding_results)
            self._store_in_qdrant(query, result)
            return result

        # Confidence evaluation
        is_confident, reason = confidence_threshold.is_confident(blended_results)

        if is_confident:
            print(f"✅ Blended result is confident. Reason: {reason}")
            result = {
                "status": reason,
                "intent": blended_results[0],
                "config_variant": ACTIVE_VARIANT
            }
        else:
            print(f"⚠ Blended result is NOT confident. Reason: {reason}")
            if blended_results and blended_results[0]['score'] >= 0.1:
                print(f"✅ Returning best available result as fallback")
                result = {
                    "status": f"FALLBACK_{reason}",
                    "intent": blended_results[0],
                    "config_variant": ACTIVE_VARIANT
                }
            else:
                print(f"⚠ No suitable results, returning generic search")
                result = {
                    "status": "FALLBACK_GENERIC",
                    "intent": {
                        "id": "SEARCH_PRODUCT",
                        "intent": "SEARCH_PRODUCT",
                        "score": 0.1,
                        "source": "fallback",
                        "reason": "generic_search_fallback"
                    },
                    "config_variant": ACTIVE_VARIANT
                }

        # ✅ Always store classification result in Qdrant
        self._store_in_qdrant(query, result)
        return result

    # ------------------------------------------------------------------
    def _handle_no_match(self, query, kw_results, emb_results):
        """Handle fallback flow when no confident match is found."""
        if emb_results:
            lower_emb = [r for r in emb_results if r['score'] >= 0.3]
            if lower_emb:
                print("✅ Fallback found embedding match with lower threshold")
                return {"status": "FALLBACK_EMBEDDING", "intent": lower_emb[0], "config_variant": ACTIVE_VARIANT}

        if kw_results:
            lower_kw = [r for r in kw_results if r['score'] >= 0.3]
            if lower_kw:
                print("✅ Fallback found keyword match with lower threshold")
                return {"status": "FALLBACK_KEYWORD", "intent": lower_kw[0], "config_variant": ACTIVE_VARIANT}

        print("⚠ No specific match found, returning generic search intent")
        return {
            "status": "FALLBACK_GENERIC",
            "intent": {
                "id": "SEARCH_PRODUCT",
                "intent": "SEARCH_PRODUCT",
                "score": 0.1,
                "source": "fallback",
                "reason": "generic_search_fallback"
            },
            "config_variant": ACTIVE_VARIANT
        }

    # ------------------------------------------------------------------
    def _blend_results(self, kw_results: List, emb_results: List) -> List[Dict]:
        """Blend keyword and embedding results using weighted average."""
        if not kw_results and not emb_results:
            return []
        if not kw_results:
            return emb_results
        if not emb_results:
            return kw_results

        intent_scores = {}
        for r in kw_results:
            intent_id = r.get('id', r.get('intent', 'unknown'))
            intent_scores[intent_id] = {'keyword_score': r.get('score', 0.0), 'embedding_score': 0.0, 'result': r}

        for r in emb_results:
            intent_id = r.get('id', r.get('intent', 'unknown'))
            if intent_id in intent_scores:
                intent_scores[intent_id]['embedding_score'] = r.get('score', 0.0)
            else:
                intent_scores[intent_id] = {'keyword_score': 0.0, 'embedding_score': r.get('score', 0.0), 'result': r}

        kw_weight = getattr(self, 'kw_weight', WEIGHTS["keyword"])
        emb_weight = getattr(self, 'emb_weight', WEIGHTS["embedding"])
        blended = []
        for intent_id, scores in intent_scores.items():
            total_score = (scores['keyword_score'] * kw_weight) + (scores['embedding_score'] * emb_weight)
            res = scores['result'].copy()
            res['score'] = total_score
            res['source'] = 'blended'
            blended.append(res)

        blended.sort(key=lambda x: x['score'], reverse=True)
        return blended

    # ------------------------------------------------------------------
    def _store_in_qdrant(self, query: str, result: Dict[str, Any]):
        """Save classified queries and embeddings to Qdrant for caching and analytics."""
        try:
            model = SentenceTransformer("all-MiniLM-L6-v2")
            vector = model.encode(query).tolist()
            store_vector(
                intent=result["intent"].get("intent", "UNKNOWN"),
                vector=vector,
                confidence=result["intent"].get("score", 0.0),
                status=result["status"],
                variant=result["config_variant"],
                query=query
            )
            print(f"✅ Stored query in Qdrant: {query}")
        except Exception as e:
            print(f"⚠ Qdrant storage failed: {e}")


# ----------------------------------------------------------------------
# Global instance for main API entrypoint
# ----------------------------------------------------------------------
_decision_engine = None


def get_intent_classification(query: str) -> Dict[str, Any]:
    """Main function for intent classification."""
    global _decision_engine
    if _decision_engine is None:
        _decision_engine = DecisionEngine()
    return _decision_engine.search(query)
