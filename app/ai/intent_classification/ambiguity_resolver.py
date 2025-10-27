"""
Ambiguity Resolver for Intent Classification (CNS-12)

Handles ambiguous and multi-intent user queries by:
1. Detecting when user input matches multiple intents (AMBIGUOUS)
2. Detecting when user input has low confidence (UNCLEAR)
3. Logging ambiguous cases for analysis
4. Providing fallback behavior

Dependencies:
- CNS-7: Uses intent definitions from intents_modular.taxonomy  
- CNS-8: Uses comprehensive keyword dictionaries (✅ Integrated)

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

# ✅ Import from CNS-8 (Keyword Dictionaries)
try:
    # Try relative import first (for module usage)
    from .keywords.loader import load_keywords
except ImportError:
    # Fallback for direct execution
    from keywords.loader import load_keywords

# ------------------ CONFIGURATION ------------------
# Standardized confidence thresholds (addresses reviewer feedback)
UNCLEAR_THRESHOLD = 0.4  # Below this = UNCLEAR (low confidence)
MIN_CONFIDENCE = 0.6     # Above this = Valid intent (medium-high confidence)
AMBIGUOUS_THRESHOLD = MIN_CONFIDENCE  # Multiple intents above this = AMBIGUOUS

LOG_FILE = "ambiguous_log.json"

# ------------------ LOAD DATA FROM CNS-8 ------------------
# Load keyword dictionaries from CNS-8
# These action codes match CNS-7 definitions (e.g., SEARCH_PRODUCT, ADD_TO_CART)
loaded_keywords = load_keywords()

# Extract action code keywords from CNS-8
INTENT_KEYWORDS = {
    action_code: details.get("keywords", [])
    for action_code, details in loaded_keywords.items()
}

# ------------------ FUNCTIONS ------------------

def log_ambiguous_case(user_input, intent_scores):
    """Log ambiguous or unclear user inputs for later review."""
    entry = {"user_input": user_input, "intent_scores": intent_scores}

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    data.append(entry)

    with open(LOG_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def calculate_confidence(user_input, keywords):
    """
    Calculate confidence score based on keyword phrase matching.
    
    Matches user input against keyword phrases from CNS-8.
    Uses exact phrase matching as defined by your teammates in CNS-8.
    
    Args:
        user_input: User's query (lowercase)
        keywords: List of keyword phrases for this action code
        
    Returns:
        float: Confidence score (0.0 to 1.0)
    """
    if not keywords:
        return 0.0
    
    user_input_lower = user_input.lower()
    
    # Count keyword phrase matches (exact phrase matching)
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
    
    Integrates CNS-7 (intent taxonomy) and CNS-8 (keyword dictionaries):
    - Uses CNS-8 keywords for matching
    - Returns CNS-7 action codes
    
    Uses standardized confidence thresholds:
    - < 0.4 (UNCLEAR_THRESHOLD): Returns UNCLEAR
    - >= 0.6 (MIN_CONFIDENCE): Valid intent
    - Multiple >= 0.6: Returns AMBIGUOUS
    
    Returns:
        dict: Contains action, confidence, and possible_intents
        - action: "UNCLEAR", "AMBIGUOUS", or specific action code from CNS-7
        - confidence: confidence score (if single intent)
        - possible_intents: all detected action codes with scores
    """
    user_input_lower = user_input.lower()
    intent_confidences = {}

    # Calculate confidence for each action code using CNS-8 keywords
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

    # Case 3: Single clear intent → Return action code from CNS-7
    final_action_code = list(high_conf_intents.keys())[0]
    return {
        "action": final_action_code,
        "confidence": high_conf_intents[final_action_code],
        "possible_intents": high_conf_intents
    }


# ------------------ MAIN (for testing) ------------------

if __name__ == "__main__":
    print("Welcome! Type your message to detect intent (type 'exit' to quit).")

    # Print summary of loaded intents
    print("\nLoaded keyword intents:")
    for intent, keywords in INTENT_KEYWORDS.items():
        print(f"  - {intent}: {len(keywords)} keywords")

    while True:
        user_input = input("\nYour input: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        result = detect_intent(user_input)
        print("Detected Result:", json.dumps(result, indent=4))
