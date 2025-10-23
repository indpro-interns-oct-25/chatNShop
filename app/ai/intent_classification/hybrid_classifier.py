# app/ai/intent_classification/hybrid_classifier.py
from typing import Dict, Any
from .embedding_matcher import EmbeddingMatcher
from .intents import INTENT_REFERENCES
from .keyword_matcher import KeywordMatcher
from ...core.config_manager import get_model_config  # must return dict for "embedding" section

class HybridClassifier:
    def __init__(self):
        cfg = get_model_config("embedding")
        self.threshold = cfg.get("intent_threshold", 0.62)
        self.use_fallback = cfg.get("fallback_to_keywords", True)
        self.matcher = EmbeddingMatcher.build_singleton(
            intents_to_refs=INTENT_REFERENCES,
            model_name=cfg.get("model_name", "sentence-transformers/all-MiniLM-L6-v2"),
            device=cfg.get("device", "auto"),
            normalize=cfg.get("normalize", True),
            intent_threshold=self.threshold,
            cache_max_entries=cfg.get("cache_max_entries", 5000),
            batch_size=cfg.get("batch_size", 32),
            top_k=cfg.get("top_k", 3),
        )
        self.keyword = KeywordMatcher()

    def classify(self, text: str) -> Dict[str, Any]:
        emb_res = self.matcher.match(text)
        if emb_res.intent is not None:
            return {
                "intent": emb_res.intent,
                "confidence": emb_res.score,
                "method": "embedding",
                "top_candidates": emb_res.top_candidates,
                "latency_ms": emb_res.took_ms,
            }
        if self.use_fallback:
            kw = self.keyword.match(text)
            if kw and kw.get("intent"):
                return {
                    "intent": kw["intent"],
                    "confidence": kw.get("confidence", 0.5),
                    "method": "keyword_fallback",
                    "top_candidates": emb_res.top_candidates,
                    "latency_ms": emb_res.took_ms + kw.get("latency_ms", 0.0),
                }
        return {
            "intent": None,
            "confidence": 0.0,
            "method": "none",
            "top_candidates": emb_res.top_candidates,
            "latency_ms": emb_res.took_ms,
        }
