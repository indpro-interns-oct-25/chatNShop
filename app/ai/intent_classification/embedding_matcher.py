import logging

class EmbeddingMatcher:
    def __init__(self, client=None):
        """
        EmbeddingMatcher handles semantic similarity searches.
        :param client: Optional vector database client (e.g., QdrantClient)
        """
        self.client = client
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def search(self, query_vector, collection_name="intents", top_k=5):
        """
        Perform semantic search using the vector database client.
        Returns a list of matches with their similarity scores.
        """
        if not self.client:
            self.logger.warning("⚠️ No vector DB client provided; returning mock search results.")
            # Mock search result for development
            return [
                {
                    "payload": {"intent": "SEARCH_PRODUCT"},
                    "score": 0.95
                }
            ]

        try:
            response = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=top_k
            )
            return response
        except Exception as e:
            self.logger.error(f"❌ Error during vector search: {e}")
            return []

    def match_intent(self, query_vector, collection_name="intents", threshold=0.7):
        """
        Finds the best matching intent for a given query vector.
        :param query_vector: Embedding vector of the query text
        :param collection_name: Name of the vector collection
        :param threshold: Minimum similarity score for a valid match
        :return: Dict with 'intent' and 'score' or None
        """
        results = self.search(query_vector, collection_name=collection_name, top_k=5)
        if not results:
            self.logger.warning("No matching results found.")
            return None

        # Handle both mock and Qdrant response formats
        best_match = max(results, key=lambda r: r["score"] if isinstance(r, dict) else r.score)
        score = best_match["score"] if isinstance(best_match, dict) else best_match.score
        intent = (
            best_match["payload"]["intent"]
            if isinstance(best_match, dict)
            else best_match.payload.get("intent", "unknown")
        )

        if score >= threshold:
            return {
                "intent": intent,
                "score": round(score, 3)
            }

        self.logger.info("🟡 No intent exceeded threshold confidence.")
        return None
