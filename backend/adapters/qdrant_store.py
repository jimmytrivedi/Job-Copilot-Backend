from backend.config import settings
from qdrant_client import QdrantClient


# Create a client
client = QdrantClient(
    url=settings.qdrant_url,
    api_key=settings.qdrant_api_key
)



