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
from typing import Callable, Dict, List, Tuple, Optional, Union
from functools import lru_cache

# --- THIS IS THE FIX ---
from app.utils.text_processing import normalize_text
from app.ai.intent_classification.keywords.loader import load_keywords
# --- END FIX ---

# Directory path for keyword JSONs
KEYWORDS_DIR = os.path.join(os.path.dirname(__file__), "keywords")

# Cache for loaded keywords
_KEYWORDS_CACHE = None


class KeywordMatcher:
    """
    A class-based wrapper for the functional keyword matcher.
    """
    def __init__(self):
        """
        Initializes the matcher and ensures keywords are loaded.
        """
        _get_cached_keywords()
        print("✅ KeywordMatcher initialized and keywords loaded.")

    def search(self, query: str) -> List[Dict]:
        """
        Runs the keyword matching logic and returns a list of results.
        """
        results = match_keywords(query, top_n=3)
        
        # Adapt output for DecisionEngine
        adapted_results = []
        for res in results:
            intent_id = res.get("intent")
            if intent_id:
                adapted_results.append({
                    "id": intent_id, 
                    "intent": intent_id,
                    "score": res.get("score", 0.0),
                    "source": "keyword",
                    "match_type": res.get("match_type"),
                    "matched_text": res.get("matched_text")
                })
        return adapted_results

# -----------------------------------------------------------------
# (All of your original functions remain below, unchanged)
# -----------------------------------------------------------------

def _score_exact() -> float:
    return 1.0

def _score_partial(overlap: int, pattern_len: int, weight: float) -> float:
    if pattern_len == 0:
        return 0.0
    return round((overlap / pattern_len) * weight, 3)

def _score_regex(match_len: int, pattern_len: int, weight: float) -> float:
    if pattern_len == 0:
        return 0.0
    return round((match_len / pattern_len) * weight, 3)

def _compile_pattern(pattern: str):
    try:
        return re.compile(pattern, re.IGNORECASE)
    except re.error:
        return None

@lru_cache(maxsize=128)
def _normalize_and_tokenize(text: str) -> Tuple[str, Tuple[str, ...]]:
    """Cache normalized text and tokens to avoid redundant processing."""
    # Enhanced normalization for special characters
    normalized = normalize_text(text)
    
    # Handle common special character patterns
    normalized = re.sub(r'[!?.,;:]+', '', normalized)  # Remove punctuation
    normalized = re.sub(r'[\'"]+', '', normalized)      # Remove quotes
    normalized = re.sub(r'[-_]+', ' ', normalized)      # Replace hyphens/underscores with space
    normalized = re.sub(r'[&]+', ' and ', normalized)    # Replace & with 'and'
    normalized = re.sub(r'[+]+', ' plus ', normalized)   # Replace + with 'plus'
    normalized = re.sub(r'[@]+', ' at ', normalized)     # Replace @ with 'at'
    normalized = re.sub(r'[#]+', ' hash ', normalized)   # Replace # with 'hash'
    normalized = re.sub(r'[$]+', ' dollar ', normalized) # Replace $ with 'dollar'
    normalized = re.sub(r'[%]+', ' percent ', normalized) # Replace % with 'percent'
    
    # Clean up multiple spaces
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    tokens = tuple(re.findall(r"\w+", normalized))
    return normalized, tokens

def _get_cached_keywords():
    global _KEYWORDS_CACHE
    if _KEYWORDS_CACHE is None:
        _KEYWORDS_CACHE = load_keywords()
    return _KEYWORDS_CACHE

def match_keywords(
    text: str,
    *,
    normalize: Union[Callable[[str], str], None] = None,
    top_n: int = 1,
) -> List[Dict]:
    if normalize is None:
        normalize = normalize_text

    raw = text.strip()
    norm_text = normalize(raw)
    if not norm_text:
        return []

    segments = re.split(r"\band\b|,|\.|!|\?|;", norm_text)
    segments = [seg.strip() for seg in segments if seg.strip()]

    keywords = _get_cached_keywords()
    candidates: List[Tuple[float, Dict]] = []
    
    seg_data = []
    for segment in segments:
        seg_tokens = set(re.findall(r"\w+", segment))
        seg_data.append((segment, seg_tokens))

    for segment, seg_tokens in seg_data:
        best_match_for_segment = None
        best_score = 0.0

        for intent, intent_data in keywords.items():
            priority = intent_data.get("priority", 1)
            keyword_list = intent_data.get("keywords", [])
            weight = 1.0 / priority
            
            for pattern in keyword_list:
                if not pattern or not isinstance(pattern, str):
                    continue

                pat_norm, pat_tokens = _normalize_and_tokenize(pattern)
                is_regex = any(ch in pattern for ch in ("\\b", "^", "$", "(", ")", "[", "]", ".*"))

                if pat_norm == segment:
                    score = _score_exact() * weight
                    match_info = {
                        "intent": intent, "action": intent, "score": score,
                        "match_type": "exact", "matched_text": pattern,
                    }
                    candidates.append((score, match_info))
                    best_match_for_segment = match_info
                    best_score = score
                    break 

                if best_match_for_segment and best_match_for_segment.get("match_type") == "exact":
                    continue

                if is_regex:
                    compiled = _compile_pattern(pattern)
                    if compiled:
                        m = compiled.search(segment)
                        if m:
                            match_len = len(m.group(0))
                            score = _score_regex(match_len, len(pattern), weight)
                            if score > best_score:
                                candidates.append((score, {
                                    "intent": intent, "action": intent, "score": score,
                                    "match_type": "regex", "matched_text": m.group(0),
                                }))
                    continue

                if pat_tokens:
                    overlap = len(seg_tokens & set(pat_tokens))
                    if overlap > 0:
                        score = _score_partial(overlap, len(pat_tokens), weight)
                        if score > best_score * 0.5: 
                            candidates.append((score, {
                                "intent": intent, "action": intent, "score": score,
                                "match_type": "partial", "matched_text": pattern,
                            }))
            
            if best_match_for_segment and best_match_for_segment.get("match_type") == "exact":
                break

    def sort_key(item: Tuple[float, Dict]) -> Tuple[float, int, int]:
        info = item[1]
        score = info.get("score", 0.0)
        match_type = info.get("match_type", "")
        typ_rank = {"exact": 3, "regex": 2, "partial": 1}.get(match_type, 0)
        return (score, typ_rank, len(str(info.get("matched_text") or "")))

    candidates.sort(key=sort_key, reverse=True)

    final_results = []
    seen_intents = set()
    for _, info in candidates:
        if info["intent"] not in seen_intents:
            final_results.append(info)
            seen_intents.add(info["intent"])

    return final_results[:top_n]


if __name__ == "__main__":
    print("Keyword matcher standalone test (may fail due to imports)")
    pass