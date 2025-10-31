"""
Ambiguity Resolver for Intent Classification (CNS-12)

Handles ambiguous and multi-intent user queries by:
1. Detecting when user input matches multiple intents (AMBIGUOUS)
2. Detecting when user input has low confidence (UNCLEAR)
3. Logging ambiguous cases for analysis
4. Providing fallback behavior

Dependencies:
- CNS-7: Uses action codes and intent structure from IntentTaxonomy
- CNS-8: Uses keyword dictionaries that align with CNS-7 action codes

Confidence Thresholds:
- UNCLEAR_THRESHOLD (0.4): Below this = unclear intent
- MIN_CONFIDENCE (0.6): Above this = valid intent
- AMBIGUOUS: Multiple intents above this = AMBIGUOUS
"""

import os
import json
import sys

# Add parent directory to path for imports when running standalone
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# ✅ Import from CNS-8 (Keyword Dictionaries aligned with CNS-7 action codes)
try:
    from .keywords.loader import load_keywords
except ImportError:
    from keywords.loader import load_keywords

# ------------------ CONFIGURATION ------------------
# Centralize thresholds via app.ai.config
try:
    from app.ai.config import UNCLEAR_THRESHOLD, MIN_CONFIDENCE
except Exception:
    UNCLEAR_THRESHOLD = 0.4
    MIN_CONFIDENCE = 0.6
AMBIGUOUS_THRESHOLD = MIN_CONFIDENCE

# Persist logs as JSON Lines for easy processing
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs")
LOG_DIR = os.path.abspath(LOG_DIR)
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "ambiguous.jsonl")

# ------------------ LOAD DATA FROM CNS-8 (aligned with CNS-7) ------------------
# Load keyword dictionaries from CNS-8
# Action codes in CNS-8 match CNS-7 IntentTaxonomy action codes
# (e.g., SEARCH_PRODUCT, ADD_TO_CART as defined in CNS-7)
loaded_keywords = load_keywords()

INTENT_KEYWORDS = {
    action_code: details.get("keywords", [])
    for action_code, details in loaded_keywords.items()
}

# ------------------ FUNCTIONS ------------------

def log_ambiguous_case(user_input, intent_scores):
    """Append ambiguous/unclear cases as JSONL for later review."""
    entry = {"user_input": user_input, "intent_scores": intent_scores}
    with open(LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def calculate_confidence(user_input, keywords):
    """
    Calculate confidence score using keywords from CNS-8.
    
    CNS-8 keywords align with CNS-7 action codes as requested by reviewer.
    
    Args:
        user_input: User's query (lowercase)
        keywords: List of keyword phrases for this action code
        
    Returns:
        float: Confidence score (0.0 to 1.0)
    """
    if not keywords:
        return 0.0
    
    user_input_lower = user_input.lower()
    
    # Count exact phrase matches
    matches = sum(1 for keyword in keywords if keyword.lower() in user_input_lower)
    
    if matches == 0:
        return 0.0
    
    # Weighted scoring: more matches = higher confidence
    # 1 match = 0.7, 2 matches = 0.85, 3+ matches = 0.95
    if matches == 1:
        return 0.7
    elif matches == 2:
        return 0.85
    else:
        return 0.95


def fallback_behavior(user_input):
    """Handle unclear or low-confidence user inputs."""
    print(f"[Fallback] Input unclear or low confidence: '{user_input}'")
    print("Sending this input to LLM or asking user for clarification...")


def detect_intent(user_input):
    """
    Detect user intent with ambiguity resolution.
    
    Uses CNS-8 keywords that align with CNS-7 action codes (as requested by reviewer).
    Returns action codes defined in CNS-7 IntentTaxonomy.
    
    Uses standardized confidence thresholds:
    - < 0.4 (UNCLEAR_THRESHOLD): Returns UNCLEAR
    - >= 0.6 (MIN_CONFIDENCE): Valid intent
    - Multiple >= 0.6: Returns AMBIGUOUS
    
    Returns:
        dict: Contains action, confidence, and possible_intents
        - action: "UNCLEAR", "AMBIGUOUS", or specific CNS-7 action code
        - confidence: confidence score (if single intent)
        - possible_intents: all detected action codes with scores
    """
    user_input_lower = user_input.lower()
    intent_confidences = {}

    # Calculate confidence for each CNS-7 action code using CNS-8 keywords
    for action_code, keywords in INTENT_KEYWORDS.items():
        confidence = calculate_confidence(user_input_lower, keywords)
        if confidence > 0:
            intent_confidences[action_code] = round(confidence, 2)

    # Filter only high-confidence intents (>= MIN_CONFIDENCE)
    high_conf_intents = {
        action_code: conf for action_code, conf in intent_confidences.items()
        if conf >= MIN_CONFIDENCE
    }

    # Case 1: No high-confidence intents → UNCLEAR
    if not high_conf_intents:
        log_ambiguous_case(user_input, {"type": "unclear", "intents": intent_confidences})
        fallback_behavior(user_input)
        return {
            "action": "UNCLEAR",
            "possible_intents": intent_confidences
        }

    # Case 2: Multiple high-confidence intents → AMBIGUOUS
    if len(high_conf_intents) > 1:
        log_ambiguous_case(user_input, {"type": "multiple", "intents": high_conf_intents})
        return {
            "action": "AMBIGUOUS",
            "possible_intents": high_conf_intents
        }

    # Case 3: Single clear intent → Return CNS-7 action code
    final_action_code = list(high_conf_intents.keys())[0]
    return {
        "action": final_action_code,
        "confidence": high_conf_intents[final_action_code],
        "possible_intents": high_conf_intents
    }


# ------------------ MAIN (for testing) ------------------

if __name__ == "__main__":
    print("Welcome! Type your message to detect intent (type 'exit' to quit).")

    # Print summary of loaded CNS-7 action codes via CNS-8 keywords
    print(f"\nLoaded {len(INTENT_KEYWORDS)} action codes from CNS-7 (via CNS-8 keywords):")
    for action_code, keywords in list(INTENT_KEYWORDS.items())[:10]:
        print(f"  - {action_code}: {len(keywords)} keywords")
    if len(INTENT_KEYWORDS) > 10:
        print(f"  ... and {len(INTENT_KEYWORDS) - 10} more action codes")

    while True:
        user_input = input("\nYour input: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        result = detect_intent(user_input)
        print("Detected Result:", json.dumps(result, indent=4))
