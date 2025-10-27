import os
import re
from typing import Callable, Dict, List, Tuple, Optional
from app.ai.intent_classification.keywords.loader import load_all_keywords
from app.utils.text_processing import normalize_text

# Directory path for keyword JSONs
KEYWORDS_DIR = os.path.join(os.path.dirname(__file__), "keywords")


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

    tokens = re.findall(r"\w+", norm_text)
    token_count = len(tokens)

    keywords = load_all_keywords(KEYWORDS_DIR)
    candidates: List[Tuple[float, Dict]] = []

    # Check each intent and its patterns
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
