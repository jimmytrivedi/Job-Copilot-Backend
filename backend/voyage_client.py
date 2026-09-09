import voyageai
import os
from dotenv import load_dotenv
import time

load_dotenv() # Reads the .env file and loads its variable into os.environ
client = voyageai.Client(api_key=os.environ.get("VOYAGE_API_KEY"))


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


def get_embeddings_by_chunks(text: str, chunk_size: int, chunk_overlap: int, input_type: str):
    chunks = chunk_by_char(text, chunk_size, chunk_overlap)
    result = client.embed(texts=chunks, model="voyage-4-large", input_type=input_type)
    return list(zip(chunks, result.embeddings))

# A Query is a single string - No need to chunk it, if it exceeds 100 chars, this splits into pices and throw away everything except first chunks.
def embed_query(text: str) -> list[float]:
    for attempt in range(3):
        try:
            result = client.embed(texts=[text], model="voyage-4-large", input_type="query")
            return  result.embeddings[0]
        except voyageai.error.RateLimitError:
            if attempt == 2:
                raise
            time.sleep(65)