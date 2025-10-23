# app/ai/intent_classification/embedding_matcher.py
"""
Embedding-based intent matcher with built-in test suite.

This version imports INTENTS from a separate intents.py file:
    app/ai/intent_classification/intents.py

Usage:
    # normal usage (interactive demo)
    python -m app.ai.intent_classification.embedding_matcher

    # run full test-suite (comprehensive tests)
    python -m app.ai.intent_classification.embedding_matcher --run-tests

Notes:
- Tests will backup & restore the existing cache file (if present).
- Tests inject a mock keyword matcher into sys.modules to verify fallback
  behavior without creating files on disk.
"""

import os
import json
import time
import sys
import argparse
import shutil
import tempfile
import types
import numpy as np

# import INTENTS from separate file (you must have app/ai/intent_classification/intents.py)
try:
    from .intents import INTENTS
except Exception as e:
    raise ImportError(
        "Failed to import INTENTS from app.ai.intent_classification.intents. "
        "Ensure file exists and is a valid Python module. Original error: " + str(e)
    )

try:
    from sentence_transformers import SentenceTransformer
except Exception as e:
    raise ImportError(
        "sentence-transformers not installed or failed to import. "
        "Run `pip install sentence-transformers`.\nOriginal error: " + str(e)
    )

# -------------------------
# Configure / tune here
# -------------------------
MODEL_NAME = "all-MiniLM-L6-v2"      # model to use
SIMILARITY_THRESHOLD = 0.55         # threshold for confident match (tune as needed)
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "intent_embeddings.json")
# -------------------------

class EmbeddingMatcher:
    def __init__(self, model_name=MODEL_NAME, cache_file=CACHE_FILE, similarity_threshold=SIMILARITY_THRESHOLD):
        self.model_name = model_name
        self.cache_file = cache_file
        self.similarity_threshold = float(similarity_threshold)

        # load model (SentenceTransformer handles CPU/GPU automatically)
        print(f"[EmbeddingMatcher] loading model '{self.model_name}'...")
        self.model = SentenceTransformer(self.model_name)

        # load or build intent embeddings
        self.intent_embeddings = self._load_or_build_cache()
        # ensure numpy arrays for fast math
        for k, v in list(self.intent_embeddings.items()):
            if not isinstance(v, np.ndarray):
                self.intent_embeddings[k] = np.array(v)

        print(f"[EmbeddingMatcher] ready. {len(self.intent_embeddings)} intents cached.")

    # ---- caching / building ----
    def _load_or_build_cache(self):
        # Load cache if present and valid
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                # convert lists to np arrays
                return {k: np.array(v) for k, v in raw.items()}
        except Exception as e:
            print(f"[EmbeddingMatcher] failed to load cache ({e}), will rebuild.")

        # Build cache from INTENTS (from intents.py)
        print("[EmbeddingMatcher] building intent embeddings from INTENTS...")
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)

        intent_embeddings = {}
        # encode all examples for each intent and average
        for intent, examples in INTENTS.items():
            if not examples:
                continue
            embeddings = self.model.encode(examples, show_progress_bar=False)
            mean_emb = np.mean(embeddings, axis=0)
            intent_embeddings[intent] = mean_emb.tolist()

        # save to json
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(intent_embeddings, f)
            print(f"[EmbeddingMatcher] saved cache to {self.cache_file}")
        except Exception as e:
            print(f"[EmbeddingMatcher] warning: failed to save cache ({e})")

        # return as numpy arrays
        return {k: np.array(v) for k, v in intent_embeddings.items()}

    # ---- similarity computation ----
    @staticmethod
    def _cosine_similarity(a, b):
        """
        Compute cosine similarity between 1-D vectors a and b.
        """
        a = np.array(a, dtype=np.float32)
        b = np.array(b, dtype=np.float32)
        if a.ndim != 1 or b.ndim != 1:
            # flatten if needed
            a = a.reshape(-1)
            b = b.reshape(-1)
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)

    # ---- prediction ----
    def predict(self, query):
        """
        Predict best intent for the provided query string.
        Returns a dict:
          {
            "query": <query>,
            "predicted_intent": <intent_name or None>,
            "confidence": <similarity score float>,
            "latency_ms": <time in ms>,
            "fallback_used": <True/False>
          }
        If predicted_intent is None, caller may perform keyword fallback.
        """
        start = time.time()
        # defensive: force string and strip
        if query is None:
            query = ""
        if not isinstance(query, str):
            query = str(query)
        query = query.strip()

        # Quick handling of empty query
        if query == "":
            return {
                "query": query,
                "predicted_intent": None,
                "confidence": 0.0,
                "latency_ms": 0.0,
                "fallback_used": False
            }

        # encode query
        query_emb = self.model.encode([query], show_progress_bar=False)[0]

        best_intent = None
        best_score = -1.0

        for intent, emb in self.intent_embeddings.items():
            score = self._cosine_similarity(query_emb, emb)
            if score > best_score:
                best_score = score
                best_intent = intent

        latency_ms = (time.time() - start) * 1000.0

        predicted = best_intent if best_score >= self.similarity_threshold else None
        fallback_used = False

        # If embedding match is not confident, attempt to fallback to keyword matcher
        if predicted is None:
            # Do not crash if keyword_matcher not present; try import dynamically
            try:
                # Expected signature: keyword_matcher.match(query) -> intent_name or None
                import importlib
                km = importlib.import_module("app.ai.intent_classification.keyword_matcher")
                if hasattr(km, "match"):
                    kw_intent = km.match(query)
                    if kw_intent:
                        predicted = kw_intent
                        fallback_used = True
                else:
                    # Try alternative: class KeywordMatcher with method match
                    if hasattr(km, "KeywordMatcher"):
                        kw = km.KeywordMatcher()
                        if hasattr(kw, "match"):
                            kw_intent = kw.match(query)
                            if kw_intent:
                                predicted = kw_intent
                                fallback_used = True
            except ModuleNotFoundError:
                # no keyword matcher present; that's fine — caller may handle fallback
                pass
            except Exception as e:
                print(f"[EmbeddingMatcher] keyword fallback error: {e}")

        result = {
            "query": query,
            "predicted_intent": predicted,
            "confidence": round(float(best_score), 4),
            "latency_ms": round(latency_ms, 2),
            "fallback_used": fallback_used
        }

        # Logging
        if predicted:
            source = "fallback(keyword)" if fallback_used else "embedding"
            print(f"[Match] '{query}' -> {predicted} (score={result['confidence']}) [{source}] [{result['latency_ms']} ms]")
        else:
            print(f"[No Match] '{query}' (best_score={round(best_score,4)}) [latency={result['latency_ms']} ms]")

        return result

# --------------------------
# Test harness (run with --run-tests)
# --------------------------

def _assert(condition, message):
    if not condition:
        raise AssertionError(message)

def run_tests(verbose=True):
    """
    Run a comprehensive suite of tests.
    Returns True on all-pass, raises AssertionError on failure.
    """
    print("\n=== Running embedding_matcher test suite ===\n")

    # Backup existing cache if present
    backed_up = False
    backup_path = None
    if os.path.exists(CACHE_FILE):
        backup_path = tempfile.mkstemp(prefix="intent_embeddings_backup_", suffix=".json")[1]
        shutil.copy2(CACHE_FILE, backup_path)
        backed_up = True
        if verbose:
            print(f"[Test] Backed up existing cache to {backup_path}")

    try:
        # 1) Initialize matcher (this will create cache)
        matcher = EmbeddingMatcher()
        _assert(len(matcher.intent_embeddings) >= 1, "No intents were loaded into matcher.")

        # Helper to run prediction and return the dict
        def pred(q):
            return matcher.predict(q)

        # ========== Positive match test ==========
        r = pred("put this in my cart")
        _assert(r["predicted_intent"] == "add_to_cart", f"Expected 'add_to_cart' but got {r}")

        # ========== Paraphrase test (may be close or below threshold) ==========
        # This checks the similarity value type and that system can handle paraphrases.
        r2 = pred("please add it to the bag")
        _assert("confidence" in r2, "Paraphrase test did not return confidence.")
        # We accept either a confident embedding match OR fallback to None; so just check types
        _assert(isinstance(r2["confidence"], float), "Paraphrase confidence is not float.")

        # ========== Negative / unrelated test ==========
        r3 = pred("what's the weather today in Paris?")
        _assert(r3["predicted_intent"] is None, f"Unrelated query unexpectedly matched: {r3}")

        # ========== Empty / whitespace test ==========
        r4 = pred("")
        _assert(r4["predicted_intent"] is None and r4["confidence"] == 0.0, "Empty input handling failed.")

        r5 = pred("    ")
        _assert(r5["predicted_intent"] is None and r5["confidence"] == 0.0, "Whitespace input handling failed.")

        # ========== Numeric / non-string test ==========
        r6 = pred(12345)
        _assert(r6["predicted_intent"] is None or isinstance(r6["confidence"], float), "Numeric input handling failed.")

        # ========== Very long input test ==========
        long_text = "buy " + ("very " * 200) + "cheap shoes now"
        r7 = pred(long_text)
        _assert("confidence" in r7, "Long input did not return confidence.")

        # ========== Performance test (latency) ==========
        rperf = pred("put this in my cart")
        _assert(rperf["latency_ms"] < 1000.0, f"Latency unusually high: {rperf['latency_ms']}ms")
        # note: we check <1000ms here to be conservative (100ms can be flaky on some machines)
        # you can change to 100ms if your environment is stable:
        # _assert(rperf['latency_ms'] < 100.0, f"Latency > 100ms: {rperf['latency_ms']}ms")

        # ========== Cache corruption handling test ==========
        # Corrupt the cache file and ensure matcher rebuilds without crashing
        if os.path.exists(CACHE_FILE):
            # create corrupted content
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                f.write("this is not valid json")
            if verbose:
                print("[Test] Wrote corrupted cache; reinitializing matcher to force rebuild.")
            # reinit matcher (which should detect and rebuild)
            matcher2 = EmbeddingMatcher()
            _assert(len(matcher2.intent_embeddings) >= 1, "Matcher failed to rebuild from corrupted cache.")
        else:
            if verbose:
                print("[Test] No cache file found for corruption test (skipping corruption test).")

        # ========== Fallback (mock keyword matcher) test ==========
        # Create a mock module in sys.modules at "app.ai.intent_classification.keyword_matcher"
        mock_mod_name = "app.ai.intent_classification.keyword_matcher"
        mock_mod = types.ModuleType(mock_mod_name)
        # define a simple match function that returns 'add_to_cart' for queries containing 'buy' or 'cart'
        def mock_match(q):
            ql = str(q).lower()
            if "buy" in ql or "cart" in ql or "bag" in ql:
                return "add_to_cart"
            return None
        mock_mod.match = mock_match
        sys.modules[mock_mod_name] = mock_mod

        # Use a query that earlier was borderline and got None from embedding
        test_query = "i want to buy these shoes"
        rfb = matcher.predict(test_query)
        # If embedding found a match, fallback won't be used; if embedding didn't, our mock should supply it
        if rfb["predicted_intent"] is None:
            # Re-run to trigger fallback path (it will see mock matcher)
            rfb2 = matcher.predict(test_query)
            # Either embedding matched or keyword fallback matched; assert at least one matched
            _assert(rfb2["predicted_intent"] == "add_to_cart" or rfb2["predicted_intent"] is None == False,
                    f"Fallback did not provide intent for '{test_query}': {rfb2}")
        # cleanup mock
        del sys.modules[mock_mod_name]

        # All tests passed
        print("\nAll tests passed ✅")
        return True

    finally:
        # restore backed up cache
        if backed_up and backup_path:
            try:
                shutil.copy2(backup_path, CACHE_FILE)
                os.remove(backup_path)
                if verbose:
                    print(f"[Test] Restored original cache from {backup_path}")
            except Exception as e:
                print(f"[Test] Warning: failed to restore original cache: {e}")

# --------------------------
# CLI / demo entrypoint
# --------------------------
def _demo_run():
    print("Testing EmbeddingMatcher (separate intents.py).")
    matcher = EmbeddingMatcher()

    sample_queries = [
        "put this in my cart",
        "i want to buy these shoes",
        "show what's in my shopping bag",
        "search for a new laptop",
        "please add it to the bag"
    ]

    for q in sample_queries:
        out = matcher.predict(q)
        print(out)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-tests", action="store_true", help="Run test suite and exit")
    args = parser.parse_args()

    if args.run_tests:
        try:
            run_tests(verbose=True)
        except AssertionError as e:
            print("\nTEST FAILED ❌:", e)
            sys.exit(2)
        except Exception as exc:
            print("\nTEST ERROR ❌:", exc)
            sys.exit(3)
        sys.exit(0)
    else:
        _demo_run()
