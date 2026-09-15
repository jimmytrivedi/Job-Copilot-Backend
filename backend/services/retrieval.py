from backend.adapters.voyage_embedder import embed_query, rerank, embed_documents
from backend.adapters.qdrant_store import client
from qdrant_client.models import PointStruct
from pathlib import Path
from backend.config import settings
from qdrant_client.models import Distance, VectorParams
from langsmith import traceable

def get_resume():
    # Reading corpus/resume.md
    path = Path(__file__).resolve().parent.parent.parent / "corpus" / "resume.md"
    return path.read_text()

# Insert vectors into a collection
def insert_vectors():
    chunks = chunk_by_char(get_resume(), settings.chunk_size, settings.chunk_overlap)
    vectors: list[list[float]] = embed_documents(chunks)
    points=[
        PointStruct(id=i, vector=vector, payload={"text": chunk})
        for i, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]

    client.upsert(
        collection_name=settings.collection_name,
        points=points
    )

def retrieve_closest_chunks(query: str, top_k: int = 5):
    query_vector = embed_query(query)
    results = client.query_points(
        collection_name=settings.collection_name,
        query=query_vector,  # type: ignore[arg-type]
        with_payload=True,
        limit=20
    )

    candidate = [p.payload.get("text", "") for p in results.points]
    top_chunks = rerank(query, candidate, top_k=top_k)

    return "\n\n".join(top_chunks)

def init_dqrant():
    # Create a new collection with not exist condition
    if not client.collection_exists(settings.collection_name):
        client.create_collection(
            collection_name=settings.collection_name,
            vectors_config=VectorParams(size=settings.vector_size, distance=Distance.COSINE)
        )
        # Insert vectors into a collection
        insert_vectors()

# Retrieve vectors into a collection
@traceable()
def query_chunks(query: str, top_k: int = 5) :
    return retrieve_closest_chunks(query, top_k)

def chunk_by_char(text: str, chunk_size: int, chunk_overlap:int):
    _chunks = []
    start_idx = 0

    while start_idx < len(text):
        end_idx = min(start_idx + chunk_size, len(text))
        chunk_text = text[start_idx:end_idx]
        _chunks.append(chunk_text)

        start_idx = (
            end_idx - chunk_overlap if end_idx < len(text) else len(text)
        )
    return _chunks