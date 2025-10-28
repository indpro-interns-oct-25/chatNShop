# tests/test_embedding_matcher_unit.py
import numpy as np
import importlib
import pytest

EM = importlib.import_module("app.ai.intent_classification.embedding_matcher")

def test_cosine_function_bounds():
    a = np.array([1.0, 0.0], dtype=np.float32)
    b = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    sims = EM._cosine_sim(a, b)
    assert pytest.approx(sims[0], rel=1e-6) == 1.0
    assert pytest.approx(sims[1], rel=1e-6) == 0.0

def test_match_with_dummy_model(monkeypatch, dummy_embeddings_file):
    # Dummy model that matches encoding shape & returns deterministic vectors
    class DummyModel:
        def __init__(self, *args, **kwargs):
            self.dim = 16
        def get_sentence_embedding_dimension(self):
            return self.dim
        def encode(self, texts, convert_to_numpy=True, show_progress_bar=False):
            out = []
            for t in texts:
                s = sum(ord(c) for c in t) % 997
                rng = np.random.RandomState(s)
                v = rng.rand(self.dim).astype(np.float32)
                v /= (np.linalg.norm(v) + 1e-12)
                out.append(v)
            return np.stack(out, axis=0)

    monkeypatch.setattr(EM, "SentenceTransformer", DummyModel, raising=False)

    # Call the match function (adjust name if your module uses a different API)
    res = EM.match_with_embeddings("checkout now", emb_file=dummy_embeddings_file, model_name="dummy", top_k=3, threshold=0.0)
    assert isinstance(res, list)
    if res:
        intent, score = res[0]
        assert isinstance(intent, str)
        assert isinstance(score, float)
