import os
import json
from typing import List, Dict, Any

class KeywordMatcher:
    """
    Handles matching user queries against keywords loaded from JSON files.
    """
    def __init__(self):
        self.keywords = self._load_keywords()
        print("KeywordMatcher Initialized: Loaded keywords dynamically.")

    def _load_keywords(self) -> Dict[str, Any]:
        """
        Loads all keyword files from the 'keywords' directory.
        """
        combined_keywords = {}
        # Correctly builds the path to the 'keywords' directory
        dir_path = os.path.join(os.path.dirname(__file__), 'keywords')
        
        # We'll focus on search_keywords for this example
        keyword_file_path = os.path.join(dir_path, 'search_keywords.json')

        if not os.path.exists(keyword_file_path):
            print(f"Warning: Keyword file not found at {keyword_file_path}")
            return {}
            
        with open(keyword_file_path, 'r') as f:
            data = json.load(f)
            # Assumes JSON format is like: {"intent": "track_order", "keywords": [...]}
            for item in data.get("intents", []):
                intent_name = item.get("intent")
                for keyword in item.get("keywords", []):
                    # Store the intent this keyword maps to
                    combined_keywords[keyword.lower()] = {
                        "intent": intent_name,
                        "score": item.get("confidence", 0.95) # Use confidence from file
                    }
        return combined_keywords

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Performs keyword search against the loaded keyword dictionary.
        Returns a result if an exact keyword match is found in the query.
        """
        query_lower = query.lower()
        
        for keyword, data in self.keywords.items():
            if keyword in query_lower:
                # Found a match, return its intent and score
                return [{
                    "id": data["intent"], 
                    "score": data["score"]
                }]
        
        return []
