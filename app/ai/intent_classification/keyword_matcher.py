"""
keyword_matcher.py
Simple, transparent keyword matcher for intent classification.
Now integrated with:
 - app.ai.intent_classification.keywords.loader
 - app.utils.text_processing
"""

from __future__ import annotations
import os
import re
from typing import Callable, Dict, List, Optional, Tuple

from app.ai.intent_classification.keywords.loader import load_all_keywords
from app.utils.text_processing import normalize_text

KEYWORDS_DIR = os.path.join(os.path.dirname(__file__), "keywords")

# ------------------------- Internal helpers -------------------------

def _compile_pattern(pat: str) -> Optional[re.Pattern]:
    try:
        return re.compile(pat, flags=re.IGNORECASE)
    except re.error:
        return None

def _score_exact() -> float:
    return 0.98

def _score_regex(match_len: int, pattern_len: int, weight: float) -> float:
    base = 0.75 + 0.15 * (match_len / max(1, pattern_len))
    return min(1.0, base * weight)

def _score_partial(token_overlap: int, token_count: int, weight: float) -> float:
    if token_count == 0:
        return 0.0
    ratio = token_overlap / token_count
    base = 0.35 + 0.5 * ratio
    return min(1.0, base * weight)

# ------------------------- Main matcher -------------------------

def match_keywords(
    text: str,
    *,
    normalize: Callable[[str], str] | None = None,
) -> List[Dict]:
    """
    Match keywords against text and return all candidate matches.
    Returns list of dicts: { intent, action, score, match_type, matched_text }
    """
    if normalize is None:
        normalize = normalize_text  # use project-level normalizer

    raw = text or ""
    norm_text = normalize(raw)
    if not norm_text:
        return []

    # Split input into segments for multi-intent detection
    segments = re.split(r"\band\b|,|\.|!|\?|;", norm_text)
    segments = [seg.strip() for seg in segments if seg.strip()]

    tokens = re.findall(r"\w+", norm_text)
    keywords = load_all_keywords(KEYWORDS_DIR)
    candidates: List[Tuple[float, Dict]] = []

    for segment in segments:
        seg_tokens = re.findall(r"\w+", segment)
        seg_token_count = len(seg_tokens)

        for intent, patterns in keywords.items():
            for entry in patterns:
                pattern = entry.get("pattern") or entry.get("keyword") or ""
                action = entry.get("action") or entry.get("action_code") or intent
                weight = float(entry.get("weight", 1.0))

                if not pattern:
                    continue

                # Detect if pattern looks like a regex
                is_regex = any(ch in pattern for ch in ("\\b", "^", "$", "(", ")", "[", "]", ".*"))

                # Exact match
                if normalize(pattern) == segment:
                    score = _score_exact() * weight
                    candidates.append((score, {
                        "intent": intent,
                        "action": action,
                        "score": score,
                        "match_type": "exact",
                        "matched_text": pattern,
                    }))
                    continue

                # Regex match
                if is_regex:
                    compiled = _compile_pattern(pattern)
                    if compiled:
                        m = compiled.search(segment)
                        if m:
                            match_len = len(m.group(0))
                            score = _score_regex(match_len, len(pattern), weight)
                            candidates.append((score, {
                                "intent": intent,
                                "action": action,
                                "score": score,
                                "match_type": "regex",
                                "matched_text": m.group(0),
                            }))
                    continue

                # Partial/token overlap
                pat_norm = normalize(pattern)
                pat_tokens = re.findall(r"\w+", pat_norm)
                if not pat_tokens:
                    continue
                overlap = len(set(seg_tokens) & set(pat_tokens))
                if overlap > 0:
                    score = _score_partial(overlap, len(pat_tokens), weight)
                    candidates.append((score, {
                        "intent": intent,
                        "action": action,
                        "score": score,
                        "match_type": "partial",
                        "matched_text": pattern,
                    }))

    # Sort candidates: score > match type > text length
    def sort_key(item: Tuple[float, Dict]) -> Tuple[float, int, int]:
        score, info = item
        typ = info.get("match_type")
        typ_rank = {"exact": 3, "regex": 2, "partial": 1}.get(typ, 0)
        return (score, typ_rank, len(str(info.get("matched_text") or "")))

    candidates.sort(key=sort_key, reverse=True)
    results = [info for _, info in candidates]  # Return all matches
    return results

# ------------------------- Local test -------------------------

if __name__ == "__main__":
    print(match_keywords("Can you add this to my cart and show specs of iPhone?"))
