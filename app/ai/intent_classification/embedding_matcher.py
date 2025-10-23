# app/ai/intent_classification/embedding_matcher.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import threading
import time
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from .similarity import cosine_sim_matrix, l2_normalize


def _resolve_device(dev: str) -> str:
    """
    Map 'auto' to an actual device supported by torch/SentenceTransformer.
    """
    if dev and dev.lower() != "auto":
        return dev
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


@dataclass
class MatchResult:
    intent: Optional[str]
    score: float
    top_candidates: List[Tuple[str, float]]
    took_ms: float
    used_fallback: bool = False


class EmbeddingMatcher:
    _instance = None
    _lock = threading.Lock()

    def __init__(
        self,
        intents_to_refs: Dict[str, List[str]],
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "auto",
        normalize: bool = True,
        intent_threshold: float = 0.62,
        cache_max_entries: int = 5000,
        batch_size: int = 32,
        top_k: int = 3,
    ):
        self.normalize = normalize
        self.intent_threshold = float(intent_threshold)
        self.batch_size = int(batch_size)
        self.top_k = int(top_k)

        resolved = _resolve_device(device)
        self.model = SentenceTransformer(model_name, device=resolved)

        # Build reference corpus
        self.intents = list(intents_to_refs.keys())
        self.ref_texts: List[str] = []
        self.ref_index_to_intent: List[str] = []
        for intent, phrases in intents_to_refs.items():
            for p in phrases:
                self.ref_texts.append(p)
                self.ref_index_to_intent.append(intent)

        # Encode and store normalized reference embeddings
        ref_emb = self.model.encode(
            self.ref_texts,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=self.normalize,
        )
        self.ref_emb = ref_emb if self.normalize else l2_normalize(ref_emb)

        # Map indices for each intent
        self.intent_max_indices: Dict[str, List[int]] = {}
        for idx, intent in enumerate(self.ref_index_to_intent):
            self.intent_max_indices.setdefault(intent, []).append(idx)

        # Simple LRU-ish cache
        self.cache: Dict[str, np.ndarray] = {}
        self.cache_keys: List[str] = []
        self.cache_max_entries = cache_max_entries

    @classmethod
    def build_singleton(cls, *args, **kwargs) -> "EmbeddingMatcher":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(*args, **kwargs)
            return cls._instance

    def _cache_put(self, text: str, emb: np.ndarray):
        self.cache[text] = emb
        self.cache_keys.append(text)
        if len(self.cache_keys) > self.cache_max_entries:
            oldest = self.cache_keys.pop(0)
            self.cache.pop(oldest, None)

    def _get_query_emb(self, text: str) -> np.ndarray:
        if text in self.cache:
            return self.cache[text]
        emb = self.model.encode(
            [text],
            batch_size=1,
            convert_to_numpy=True,
            normalize_embeddings=self.normalize,
        )[0]
        if not self.normalize:
            emb = l2_normalize(emb.reshape(1, -1))[0]
        self._cache_put(text, emb)
        return emb

    def match(self, text: str) -> MatchResult:
        t0 = time.perf_counter()
        q = self._get_query_emb(text).reshape(1, -1)
        sims = cosine_sim_matrix(q, self.ref_emb, already_normalized=True).flatten()

        # Aggregate: best similarity per intent
        best_per_intent: Dict[str, float] = {}
        for intent, indices in self.intent_max_indices.items():
            best_per_intent[intent] = float(sims[indices].max()) if indices else -1.0

        ranked = sorted(best_per_intent.items(), key=lambda x: x[1], reverse=True)
        top = ranked[: self.top_k]
        best_intent, best_score = top[0]
        took_ms = (time.perf_counter() - t0) * 1000.0

        intent_out: Optional[str] = best_intent if best_score >= self.intent_threshold else None
        return MatchResult(intent=intent_out, score=best_score, top_candidates=top, took_ms=took_ms)
