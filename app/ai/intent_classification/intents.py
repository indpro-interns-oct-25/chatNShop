"""
intents.py
Central intent management module.

This module provides helper utilities to:
- Load all defined intents and their action codes.
- Retrieve descriptions and example phrases.
- Match example user phrases to intents (basic lookup).
"""

from typing import Optional, Dict, List
from .intents_modular.enums import Intent
# from .intents_modular.models import IntentExample
from .intents_modular.taxonomy import ACTION_CODE_MAP
# from .intents_modular.examples import INTENT_EXAMPLES


class IntentManager:
    """Manages all available intents and their action codes."""

    def __init__(self):
        self.intents = list(Intent)
        self.action_map = ACTION_CODE_MAP
        # self.examples = INTENT_EXAMPLES

    def get_all_intents(self) -> List[Intent]:
        """Return all available intents."""
        return self.intents

    def get_action_code(self, intent: Intent) -> Optional[str]:
        """Return the standardized action code for a given intent."""
        return self.action_map.get(intent)

    # def get_examples(self, intent: Intent) -> List[str]:
    #     """Return example phrases for a given intent."""
    #     return [ex.phrase for ex in self.examples if ex.intent == intent]

    def find_intent_by_phrase(self, phrase: str) -> Optional[Dict[str, str]]:
        """
        Find the intent corresponding to an example phrase.
        This is a simple lookup (not ML-based).
        """
        for ex in self.examples:
            if ex.phrase.lower() == phrase.lower():
                return {
                    "intent": ex.intent.value,
                    "action_code": ex.action_code
                }
        return None

    def describe(self) -> List[Dict[str, str]]:
        """
        Return a list of all intents with their action codes and sample examples.
        Useful for debugging or visualization.
        """
        data = []
        for intent in self.intents:
            data.append({
                "intent": intent.value,
                "action_code": self.get_action_code(intent),
                "examples": self.get_examples(intent)
            })
        return data


# Example singleton instance
intent_manager = IntentManager()

if __name__ == "__main__":
    # Simple test to verify everything works
    print("✅ Total intents loaded:", len(intent_manager.get_all_intents()))
    print("🔍 Example lookup:", intent_manager.find_intent_by_phrase("Add this to my cart"))
    print("📘 Description sample:", intent_manager.describe()[:3])
