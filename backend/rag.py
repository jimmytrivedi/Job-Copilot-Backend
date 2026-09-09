from qdrant_client import QdrantClient
from backend.voyage_client import get_embeddings_by_chunks, embed_query
from qdrant_client.models import PointStruct, Document
import os

def get_resume():
    # Reading corpus/resume.md
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base, "corpus/resume.md"), "r") as f:
        text = f.read()
    return text

# Insert vectors into a collection
def insert_vectors(client: QdrantClient):
    embeddings = get_embeddings_by_chunks(get_resume(), 500, 50, input_type="document")
    points=[
        PointStruct(id=i, vector=vector, payload={"text": chunk})
        for i, (chunk, vector) in enumerate(embeddings)
    ]

    client.upsert(
        collection_name="test_collection",
        points=points
    )

def retrieve_closest_chunks(client: QdrantClient, query: str):
    query_vector = embed_query(query)
    results = client.query_points(
        collection_name="test_collection",
        query=query_vector,
        with_payload=True,
        limit=5
    )

    total  = ""
    for point in results.points:
        total += point.payload.get("text", "") + "\n\n"

    return total