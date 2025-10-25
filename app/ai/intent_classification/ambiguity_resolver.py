import os
import json

# ✅ Import the keyword loader from the keywords folder
from keywords.loader import load_keywords

# ------------------ CONFIGURATION ------------------
MIN_CONFIDENCE = 0.6
LOG_FILE = "ambiguous_log.json"

# ------------------ LOAD KEYWORDS ------------------
# Dynamically load all keyword JSONs using the loader script
loaded_data = load_keywords()

# Extract intent keywords and priorities from loaded data
INTENT_KEYWORDS = {
    intent: details.get("keywords", [])
    for intent, details in loaded_data.items()
}

# Sort intents based on their "priority" value (lower = higher priority)
INTENT_PRIORITY = sorted(
    loaded_data.keys(),
    key=lambda intent: loaded_data[intent].get("priority", 999)
)

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


def calculate_confidence(user_words, keywords):
    """Simple confidence measure: how many words match keywords."""
    matches = sum(1 for word in user_words if word in keywords)
    return matches / len(user_words) if user_words else 0


def fallback_behavior(user_input):
    """Handle unclear or low-confidence user inputs."""
    print(f"[Fallback] Input unclear or low confidence: '{user_input}'")
    print("Sending this input to LLM or asking user for clarification...")


def detect_intent(user_input):
    """Detect the most likely intent based on keyword matching."""
    user_words = user_input.lower().split()
    intent_confidences = {}

    # Calculate confidence for each intent
    for intent, keywords in INTENT_KEYWORDS.items():
        confidence = calculate_confidence(user_words, keywords)
        if confidence > 0:
            intent_confidences[intent] = round(confidence, 2)

    # Filter only high-confidence intents
    high_conf_intents = {
        intent: conf for intent, conf in intent_confidences.items()
        if conf >= MIN_CONFIDENCE
    }

    # If no confident intent found → log & fallback
    if not high_conf_intents:
        log_ambiguous_case(user_input, intent_confidences)
        fallback_behavior(user_input)
        return {
            "action": "UNCLEAR",
            "possible_intents": intent_confidences
        }

    # If multiple high-confidence intents → log & return all
    if len(high_conf_intents) > 1:
        log_ambiguous_case(user_input, {"type": "multiple", "intents": high_conf_intents})
        return {
            "action": "AMBIGUOUS",
            "possible_intents": high_conf_intents
        }

    # Single clear intent → return that
    final_intent = list(high_conf_intents.keys())[0]
    return {
        "action": final_intent,
        "confidence": high_conf_intents[final_intent],
        "all_high_conf_intents": high_conf_intents
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
