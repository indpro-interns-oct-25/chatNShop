from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")
print("✅ Connected to Qdrant successfully!")
print("Collections:", client.get_collections())
