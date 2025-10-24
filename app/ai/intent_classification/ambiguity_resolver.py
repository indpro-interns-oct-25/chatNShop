import json
import os

MIN_CONFIDENCE = 0.6
LOG_FILE = "ambiguous_log.json"

INTENT_KEYWORDS = {
    "ADD_TO_CART": ["add", "cart", "buy", "purchase", "put", "order", "shop", "item", "product", "dress"],
    "VIEW_CART": ["show", "view", "cart", "my", "display", "bag", "items"],
    "CHECKOUT": ["checkout", "pay", "purchase", "buy", "order", "confirm", "proceed"],
    "SEARCH": ["search", "find", "look", "show", "explore", "find me", "searching"],
    "PRODUCT_INFO": ["details", "info", "information", "specs", "description", "about", "features"],
    "COMPARE": ["compare", "difference", "vs", "versus", "similar", "contrast"],
}

INTENT_PRIORITY = ["CHECKOUT", "ADD_TO_CART", "VIEW_CART", "SEARCH", "PRODUCT_INFO", "COMPARE"]

def log_ambiguous_case(user_input, intent_scores):
    entry = {"user_input": user_input, "intent_scores": intent_scores}
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    else:
        data = []
    data.append(entry)
    with open(LOG_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

def calculate_confidence(user_words, keywords):
    matches = sum(1 for word in user_words if word in keywords)
    return matches / len(user_words) if user_words else 0

def fallback_behavior(user_input):
    print(f"[Fallback] Input unclear or low confidence: '{user_input}'")
    print("Sending this input to LLM or asking user for clarification...")

def detect_intent(user_input):
    user_words = user_input.lower().split()
    intent_confidences = {}

    for intent, keywords in INTENT_KEYWORDS.items():
        confidence = calculate_confidence(user_words, keywords)
        if confidence > 0:
            intent_confidences[intent] = round(confidence, 2)

    high_conf_intents = {i: c for i, c in intent_confidences.items() if c >= MIN_CONFIDENCE}

    if not high_conf_intents:
        log_ambiguous_case(user_input, intent_confidences)
        fallback_behavior(user_input)
        return {"action": "UNCLEAR", "possible_intents": intent_confidences}

    if len(high_conf_intents) > 1:
        # Multiple high-confidence intents detected.
        # Instead of interactive disambiguation here, return all candidates so
        # upstream code can decide how to handle ambiguity (e.g., ask the user,
        # call an LLM clarifier, or present choices). Also log the case.
        log_ambiguous_case(user_input, {"type": "multiple", "intents": high_conf_intents})
        return {"action": "AMBIGUOUS", "possible_intents": high_conf_intents}

    final_intent = list(high_conf_intents.keys())[0]
    return {"action": final_intent, "confidence": high_conf_intents[final_intent], "all_high_conf_intents": high_conf_intents}

if __name__ == "__main__":
    print("Welcome! Type your message to detect intent (type 'exit' to quit).")
    while True:
        user_input = input("\nYour input: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        result = detect_intent(user_input)
        print("Detected Result:", json.dumps(result, indent=4))
