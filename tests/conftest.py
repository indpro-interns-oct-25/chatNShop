# tests/conftest.py
import os
import sys
import pathlib
import json
import numpy as np
import pytest

# ---------- adjust this if your repo layout differs ----------
# We assume repo root is the parent of the folder that contains `app/` and `tests/`.
HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent  # tests/ and app/ are siblings under repo root
# If tests are at repo root/tests and app/ is at repo_root/app, this works.
# If your layout differs, adjust REPO_ROOT accordingly.

# Add repo root to sys.path so imports like `from app.ai...` work
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Optionally, you can print for debug (comment out for CI)
# print("Added to PYTHONPATH:", str(REPO_ROOT))

# ---------- fixtures used by tests (examples) ----------
@pytest.fixture(scope="session")
def tmp_keywords_dir(tmp_path_factory):
    """
    Create temporary keywords JSON files used by tests.
    Tests will point KeywordMatcher at this dir (if they use fixture).
    """
    d = tmp_path_factory.mktemp("kwdir")
    search = {
        "SEARCH_PRODUCT": ["search product", "find product", "look for product", "product search"],
        "SEARCH_CATEGORY": ["search category", "browse category", "find category"]
    }
    cart = {
        "ADD_TO_CART": ["add to cart", "put in cart", "buy now", "add item"],
        "REMOVE_FROM_CART": ["remove from cart", "delete item", "remove product"]
    }
    product = {
        "PRODUCT_INFO": ["product info", "product details", "tell me about", "what is this"],
        "PRODUCT_PRICE": ["price", "how much", "cost", "price info"]
    }
    (d / "search_keywords.json").write_text(json.dumps(search, ensure_ascii=False), encoding="utf-8")
    (d / "cart_keywords.json").write_text(json.dumps(cart, ensure_ascii=False), encoding="utf-8")
    (d / "product_keywords.json").write_text(json.dumps(product, ensure_ascii=False), encoding="utf-8")
    return str(d)

@pytest.fixture
def dummy_embeddings_file(tmp_path, tmp_keywords_dir):
    """
    Create deterministic small embeddings .npz file compatible with embedding tests.
    """
    intents = []
    import os, json
    for fname in os.listdir(tmp_keywords_dir):
        if fname.endswith(".json"):
            with open(os.path.join(tmp_keywords_dir, fname), "r", encoding="utf-8") as f:
                data = json.load(f)
                intents.extend(sorted(list(data.keys())))
    intents = sorted(set(intents))
    dim = 16
    embs = []
    for intent in intents:
        seed = sum(ord(c) for c in intent) % 997
        import numpy as _np
        rng = _np.random.RandomState(seed)
        v = rng.rand(dim).astype(_np.float32)
        v /= (_np.linalg.norm(v) + 1e-12)
        embs.append(v)
    embs = _np.stack(embs, axis=0)
    out = tmp_path / "intent_embeddings_test.npz"
    _np.savez_compressed(str(out), intents=_np.array(intents, dtype=object), embeddings=embs, meta=json.dumps({}))
    return str(out)
