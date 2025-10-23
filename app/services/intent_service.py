# app/services/intent_service.py
from typing import Dict, Any
from ..ai.intent_classification.hybrid_classifier import HybridClassifier

_classifier = HybridClassifier()

def classify_intent(user_text: str) -> Dict[str, Any]:
    return _classifier.classify(user_text)
