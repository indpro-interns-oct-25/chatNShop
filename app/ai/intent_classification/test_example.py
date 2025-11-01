"""Example usage of the keyword matching system."""

from app.ai.intent_classification.keyword_matcher import KeywordMatcher


# Minimal local ScoringEngine for example/demo purposes. The project has
# a separate scoring module; this lightweight class avoids import issues
# during test collection and provides the methods used in this example.
class ScoringEngine:
    def __init__(self, base_threshold: float = 0.5):
        self.base_threshold = base_threshold

    def process_scores(self, scores):
        # Expect scores as a list of dicts with 'intent' and 'score'
        return [(s.get('intent'), s.get('score', 0.0)) for s in (scores or []) if s.get('score', 0.0) >= self.base_threshold]

    def get_top_intent(self, scores):
        if not scores:
            return ("unknown", 0.0)
        best = max(scores, key=lambda s: s.get('score', 0.0))
        return (best.get('intent'), best.get('score', 0.0))

def main():
    # Initialize the components
    matcher = KeywordMatcher()
    scorer = ScoringEngine(base_threshold=0.5)
    
    # Test queries
    queries = [
        "show me red running shoes",
        "where's my order status??",
        "i want to update my shipping address",
        "help me track order #12345"
    ]
    
    for query in queries:
        print(f"\nProcessing query: '{query}'")

        # Get matches and scores using the KeywordMatcher API
        scores = matcher.search(query)

        # Get all intents above threshold
        matches = scorer.process_scores(scores)
        
        # Print results
        print("Matches:")
        for intent, score in matches:
            print(f"  - {intent}: {score:.2f}")
            
        # Get top intent
        top_intent, confidence = scorer.get_top_intent(scores)
        if top_intent != "unknown":
            print(f"Top Intent: {top_intent} (confidence: {confidence:.2f})")
        else:
            print("No matching intent found")

if __name__ == "__main__":
    main()