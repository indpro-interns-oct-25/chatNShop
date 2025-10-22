from typing import List, Dict, Any

class EmbeddingMatcher:
    """
    A realistic mock for the embedding (semantic) search service.
    It simulates connecting to a vector database like Qdrant without
    using any pre-defined sample data.
    """
    def __init__(self):
        # In a real application, this would initialize a connection to Qdrant.
        # self.qdrant_client = QdrantClient(...)
        print("EmbeddingMatcher Initialized (realistic mock).")

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Simulates performing a semantic search. The logic here is designed
        to produce plausible results based on the query's content.
        """
        print(f"--- Simulating EMBEDDING search for: '{query}' ---")
        query_lower = query.lower()

        # Simulate finding semantically similar intents based on keywords
        if "watch" in query_lower or "fitness" in query_lower or "wearable" in query_lower:
            # If the query is about wearables, return product-related intents
            return [
                {"id": "find_product", "score": 0.90},
                {"id": "product_comparison", "score": 0.85},
            ]
        
        if "cancel" in query_lower or "return" in query_lower or "exchange" in query_lower:
             # If the query is about returns, return order-management intents
            return [
                {"id": "return_policy", "score": 0.92},
                {"id": "cancel_order", "score": 0.88},
            ]
            
        # If no strong semantic signal, return a generic fallback
        if len(query_lower) > 5:
             return [{"id": "general_inquiry", "score": 0.75}]

        return []
