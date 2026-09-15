import voyageai
from backend.config import settings
import time

client = voyageai.Client(api_key=settings.voyage_api_key)

# A Query is a single string - No need to chunk it, if it exceeds 100 chars, this splits into pices and throw away everything except first chunks.
def embed_query(text: str) -> list[float | int]:
    for attempt in range(5):
        try:
            result = client.embed(texts=[text], model=settings.embed_model, input_type=settings.input_type_query)
            return  result.embeddings[0]
        except voyageai.error.RateLimitError:
            if attempt == 4:
                raise
            time.sleep(25)  # 3 RPM free tier needs ~20s spacing between calls
    raise RuntimeError("embed_query_failed")

def embed_documents(texts: list[str]) -> list[list[float]]:
    result = client.embed(texts=texts, model=settings.embed_model, input_type=settings.input_type_document)
    return result.embeddings

def rerank(query: str, documents: list[str], top_k: int = 5) -> list[str]:
    result = client.rerank(
        query=query,
        documents=documents,
        model=settings.rerank_model,
        top_k=top_k
    )
    return [r.document for r in result.results]