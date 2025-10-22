"""keyword_matcher.py

This module implements a simple, easy-to-read keyword matcher used by the
intent classification pipeline. The goal was to be explicit and readable so
you can inspect, test and later replace parts with project-specific
implementations (normalizer, scoring module, or an indexed matcher).

Key responsibilities implemented here:
- Load keyword patterns from JSON files in the `keywords` directory.
- Normalize incoming text (default normalizer is simple; you can pass your
    project's normalizer as the `normalize` argument to `match_keywords`).
- Support three matching strategies:
    * exact (normalized string equality)
    * regex (patterns treated as regex when they contain regex-like symbols)
    * partial/token-overlap (basic set intersection of tokens)
- Produce a small scored candidate list with tie-breaking rules.

Note: this file is intentionally small and dependency-free so it can be
inspected and tested independently. Integration with a central `scoring.py`
or a normalization utility is straightforward and left as a follow-up.
"""
from __future__ import annotations

import json
import os
import re
from typing import Callable, Dict, List, Optional, Tuple

KEYWORDS_DIR = os.path.join(os.path.dirname(__file__), "keywords")


def _default_normalize(text: str) -> str:
    """A very small default normalizer.

    Strips surrounding whitespace and lower-cases the input. The project
    probably has a more sophisticated normalizer (lemmatization, unicode
    normalization, removing stopwords, etc.). Pass that in via the
    `normalize` parameter to `match_keywords`.
    """
    return (text or "").strip().lower()


def _load_keywords_from_file(path: str) -> Dict[str, List[dict]]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            # Expecting { intent_name: [ {pattern, action, weight?}, ... ] }
            return data or {}
    except FileNotFoundError:
        return {}
    except Exception:
        # If JSON invalid, return empty to avoid crashing
        return {}


def _load_all_keywords() -> Dict[str, List[dict]]:
    result: Dict[str, List[dict]] = {}
    for fname in ("search_keywords.json", "product_keywords.json", "cart_keywords.json"):
        path = os.path.join(KEYWORDS_DIR, fname)
        data = _load_keywords_from_file(path)
        for intent, patterns in data.items():
            result.setdefault(intent, []).extend(patterns)
    return result


# We avoid global heavy-weight caches here to keep the module predictable
# for tests and interactive inspection. For production, consider caching the
# result of _load_all_keywords and pre-compiling regexes at module load.


def _compile_pattern(pat: str) -> Optional[re.Pattern]:
    try:
        return re.compile(pat, flags=re.IGNORECASE)
    except re.error:
        return None


def _score_exact() -> float:
    return 0.98


def _score_regex(match_len: int, pattern_len: int, weight: float) -> float:
    # Give regex matches a relatively high baseline. We slightly boost the
    # score according to how much of the pattern was matched (match_len / pattern_len)
    # and then apply the optional pattern-level weight to allow some patterns
    # to influence confidence.
    base = 0.75 + 0.15 * (match_len / max(1, pattern_len))
    return min(1.0, base * weight)


def _score_partial(token_overlap: int, token_count: int, weight: float) -> float:
    if token_count == 0:
        return 0.0
    ratio = token_overlap / token_count
    # Partial matches receive a lower baseline than regex/exact matches.
    # We scale by the token overlap ratio so that patterns with more shared
    # tokens with the user text score higher.
    base = 0.35 + 0.5 * ratio
    return min(1.0, base * weight)


def match_keywords(
    text: str,
    *,
    normalize: Callable[[str], str] | None = None,
    top_n: int = 1,
) -> List[Dict]:
    """
    Match keywords against text and return top_n candidates.

    Returns list of dicts with keys: intent, action, score, match_type, matched_text
    """
    if normalize is None:
        normalize = _default_normalize

    raw = text or ""
    norm_text = normalize(raw)
    if not norm_text:
        return []

    tokens = [t for t in re.findall(r"\w+", norm_text)]
    token_count = len(tokens)

    keywords = _load_all_keywords()
    candidates: List[Tuple[float, Dict]] = []

    for intent, patterns in keywords.items():
        for entry in patterns:
            pattern = entry.get("pattern") or entry.get("keyword") or ""
            action = entry.get("action") or entry.get("action_code") or intent
            weight = float(entry.get("weight", 1.0))

            if not pattern:
                continue

            # Try regex: if pattern looks like a regex (contains \b, ^, $, or parentheses) we treat it as regex
            # Heuristic to detect regex-like patterns. This is simple and
            # intentionally permissive for the test fixtures. If you prefer
            # deterministic behavior, add an explicit `is_regex` boolean in
            # the keyword JSON and use it here.
            is_regex = any(ch in pattern for ch in ("\\b", "^", "$", "(", ")", "[", "]", ".*"))

            # Exact match
            if normalize(pattern) == norm_text:
                candidates.append((
                    _score_exact() * weight,
                    {
                        "intent": intent,
                        "action": action,
                        "score": _score_exact() * weight,
                        "match_type": "exact",
                        "matched_text": pattern,
                    },
                ))
                continue

            # Regex match
            if is_regex:
                compiled = _compile_pattern(pattern)
                if compiled:
                    # We search against the original raw text so capture groups
                    # and token boundaries behave as the pattern author expects.
                    m = compiled.search(raw)
                    if m:
                        match_len = len(m.group(0))
                        score = _score_regex(match_len, len(pattern), weight)
                        candidates.append((
                            score,
                            {
                                "intent": intent,
                                "action": action,
                                "score": score,
                                "match_type": "regex",
                                "matched_text": m.group(0),
                            },
                        ))
                continue

            # Partial/token overlap matching
            pat_norm = normalize(pattern)
            pat_tokens = [t for t in re.findall(r"\w+", pat_norm)]
            if not pat_tokens:
                continue
            overlap = len(set(tokens) & set(pat_tokens))
            if overlap > 0:
                score = _score_partial(overlap, len(pat_tokens), weight)
                candidates.append((
                    score,
                    {
                        "intent": intent,
                        "action": action,
                        "score": score,
                        "match_type": "partial",
                        "matched_text": pattern,
                    },
                ))

    # Sort candidates by score desc, then match_type preference (exact>regex>partial), then matched_text length
    def sort_key(item: Tuple[float, Dict]) -> Tuple[float, int, int]:
        score, info = item
        typ = info.get("match_type")
        typ_rank = {"exact": 3, "regex": 2, "partial": 1}.get(typ, 0)
        return (score, typ_rank, len(str(info.get("matched_text") or "")))

    candidates.sort(key=sort_key, reverse=True)
    results = [info for _, info in candidates][:max(0, int(top_n))]
    return results
