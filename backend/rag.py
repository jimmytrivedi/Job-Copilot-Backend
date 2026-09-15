from qdrant_client import QdrantClient
from backend.voyage_client import get_embeddings_by_chunks, embed_query, rerank
from qdrant_client.models import PointStruct, Document
from pathlib import Path

def get_resume():
    # Reading corpus/resume.md
    path = Path(__file__).resolve().parent.parent / "corpus" / "resume.md"
    return path.read_text()

# Insert vectors into a collection
def insert_vectors(client: QdrantClient):
    embeddings = get_embeddings_by_chunks(get_resume(), 500, 50, input_type="document")
    points=[
        PointStruct(id=i, vector=vector, payload={"text": chunk})
        for i, (chunk, vector) in enumerate(embeddings)
    ]

    client.upsert(
        collection_name="resume",
        points=points
    )

def retrieve_closest_chunks(client: QdrantClient, query: str, top_k: int = 5):
    query_vector = embed_query(query)
    results = client.query_points(
        collection_name="resume",
        query=query_vector,  # type: ignore[arg-type]
        with_payload=True,
        limit=20
    )

    candidate = [p.payload.get("text", "") for p in results.points]
    top_chunks = rerank(query, candidate, top_k=top_k)

    return "\n\n".join(top_chunks)