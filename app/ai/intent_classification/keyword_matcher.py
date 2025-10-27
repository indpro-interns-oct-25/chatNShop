from .config_manager import ConfigManager

config = ConfigManager()
KEYWORDS = config.get_keywords()
def match_keywords(text):
    for intent, words in KEYWORDS.items():
        for word in words:
            if word in text.lower():
                return intent
    return "unknown"
import os
import re
from typing import Callable, Dict, List, Tuple, Optional
from functools import lru_cache
from app.ai.intent_classification.keywords.loader import load_keywords
from app.utils.text_processing import normalize_text

# Directory path for keyword JSONs
KEYWORDS_DIR = os.path.join(os.path.dirname(__file__), "keywords")

# Cache for loaded keywords
_KEYWORDS_CACHE = None


# ------------------------- Internal scoring helpers -------------------------

def _score_exact() -> float:
    """Return a high score for exact matches."""
    return 1.0


def _score_partial(overlap: int, pattern_len: int, weight: float) -> float:
    """Score partial matches based on token overlap."""
    if pattern_len == 0:
        return 0.0
    return round((overlap / pattern_len) * weight, 3)


def _score_regex(match_len: int, pattern_len: int, weight: float) -> float:
    """Score regex matches based on matched length."""
    if pattern_len == 0:
        return 0.0
    return round((match_len / pattern_len) * weight, 3)


def _compile_pattern(pattern: str):
    """Safely compile regex pattern."""
    try:
        return re.compile(pattern, re.IGNORECASE)
    except re.error:
        return None


@lru_cache(maxsize=128)
def _normalize_and_tokenize(text: str) -> Tuple[str, Tuple[str, ...]]:
    """Cache normalized text and tokens to avoid redundant processing."""
    normalized = normalize_text(text)
    tokens = tuple(re.findall(r"\w+", normalized))
    return normalized, tokens


def _get_cached_keywords():
    """Load keywords once and cache them."""
    global _KEYWORDS_CACHE
    if _KEYWORDS_CACHE is None:
        _KEYWORDS_CACHE = load_keywords()
    return _KEYWORDS_CACHE


# ------------------------- Main matching function -------------------------

def match_keywords(
    text: str,
    *,
    normalize: Callable[[str], str] | None = None,
    top_n: int = 1,
) -> List[Dict]:
    """
    Match keywords against text and return all candidate matches.

    Returns list of dicts: { intent, action, score, match_type, matched_text }
    """
    if normalize is None:
        normalize = normalize_text

    raw = text.strip()
    norm_text = normalize(raw)
    if not norm_text:
        return []

    # Split input into segments for multi-intent detection
    segments = re.split(r"\band\b|,|\.|!|\?|;", norm_text)
    segments = [seg.strip() for seg in segments if seg.strip()]

    keywords = _get_cached_keywords()
    candidates: List[Tuple[float, Dict]] = []
    
    # Pre-tokenize all segments once
    seg_data = []
    for segment in segments:
        seg_tokens = set(re.findall(r"\w+", segment))
        seg_data.append((segment, seg_tokens))

    # Pre-tokenize all segments once
    seg_data = []
    for segment in segments:
        seg_tokens = set(re.findall(r"\w+", segment))
        seg_data.append((segment, seg_tokens))

    # Check each intent and its patterns
    for segment, seg_tokens in seg_data:
        best_match_for_segment = None
        best_score = 0.0

        for intent, intent_data in keywords.items():
            # Get priority and keywords list from the intent data
            priority = intent_data.get("priority", 1)
            keyword_list = intent_data.get("keywords", [])
            weight = 1.0 / priority  # Higher priority = higher weight
            
            for pattern in keyword_list:
                if not pattern or not isinstance(pattern, str):
                    continue

                # Use cached normalization
                pat_norm, pat_tokens = _normalize_and_tokenize(pattern)
                
                # Detect if pattern looks like a regex
                is_regex = any(ch in pattern for ch in ("\\b", "^", "$", "(", ")", "[", "]", ".*"))

                # Exact match - highest priority
                if pat_norm == segment:
                    score = _score_exact() * weight
                    match_info = {
                        "intent": intent,
                        "action": intent,
                        "score": score,
                        "match_type": "exact",
                        "matched_text": pattern,
                    }
                    # Exact match found, add immediately and move to next segment
                    candidates.append((score, match_info))
                    best_match_for_segment = match_info
                    best_score = score
                    break  # Found exact match, no need to check other patterns

                # Skip regex and partial if we already have an exact match
                if best_match_for_segment and best_match_for_segment.get("match_type") == "exact":
                    continue

                # Regex match
                if is_regex:
                    compiled = _compile_pattern(pattern)
                    if compiled:
                        m = compiled.search(segment)
                        if m:
                            match_len = len(m.group(0))
                            score = _score_regex(match_len, len(pattern), weight)
                            if score > best_score:
                                candidates.append((score, {
                                    "intent": intent,
                                    "action": intent,
                                    "score": score,
                                    "match_type": "regex",
                                    "matched_text": m.group(0),
                                }))
                    continue

                # Partial/token overlap - only if tokens exist
                if pat_tokens:
                    overlap = len(seg_tokens & set(pat_tokens))
                    if overlap > 0:
                        score = _score_partial(overlap, len(pat_tokens), weight)
                        if score > best_score * 0.5:  # Only consider if score is reasonable
                            candidates.append((score, {
                                "intent": intent,
                                "action": intent,
                                "score": score,
                                "match_type": "partial",
                                "matched_text": pattern,
                            }))
            
            # If we found an exact match for this intent, break to next segment
            if best_match_for_segment and best_match_for_segment.get("match_type") == "exact":
                break

    # Sort candidates: score > match type > text length
    def sort_key(item: Tuple[float, Dict]) -> Tuple[float, int, int]:
        info = item[1]
        score = info.get("score", 0.0)
        match_type = info.get("match_type", "")
        typ_rank = {"exact": 3, "regex": 2, "partial": 1}.get(match_type, 0)
        return (score, typ_rank, len(str(info.get("matched_text") or "")))

    candidates.sort(key=sort_key, reverse=True)

    results = [info for _, info in candidates]  # Return all matches
    return results


# ------------------------- Local test -------------------------
if __name__ == "__main__":
    print(match_keywords("Can you add this to my cart?"))
    print(match_keywords("Can you add this to my cart and show specs of iPhone?"))
