from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv
from qdrant_client.models import Distance, VectorParams
from backend.rag import insert_vectors, retrieve_closest_chunks

load_dotenv()

# Create a client
client = QdrantClient(
    url=os.environ.get("QDRANT_DB_URL"),
    api_key=os.environ.get("QDRANT_API_KEY")
)

def init_dqrant():
    # Create a new collection with not exist condition
    if not client.collection_exists("test_collection"):
        client.create_collection(
            collection_name="test_collection",
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
        )
        # Insert vectors into a collection
        insert_vectors(client)

# Retrieve vectors into a collection
def query_chunks(query: str, top_k: int = 5) :
    return retrieve_closest_chunks(client, query, top_k)



