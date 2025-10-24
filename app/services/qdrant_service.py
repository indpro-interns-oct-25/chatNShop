from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from app.core.config import settings

QDRANT_COLLECTION_NAME = "products"
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'

class QdrantService:
    def __init__(self):
        self.qdrant = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
        # Load the model only once
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    # --- THIS FUNCTION MUST BE INDENTED ---
    def search(self, query: str, limit: int = 5):
        vector = self.model.encode(query).tolist()
        search_result = self.qdrant.search(
            collection_name=QDRANT_COLLECTION_NAME,
            query_vector=vector,
            limit=limit,
            with_payload=True,
            score_threshold=0.5  # Filter for good matches
        )
        return search_result

# Create a single, reusable instance
qdrant_service = QdrantService()