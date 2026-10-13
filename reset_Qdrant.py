import os
from qdrant_client import QdrantClient

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "chatuas_qdrant_store"

client = QdrantClient(url=QDRANT_URL)
client.delete_collection(COLLECTION_NAME)

print(f"Collection: {COLLECTION_NAME} gelöscht")
