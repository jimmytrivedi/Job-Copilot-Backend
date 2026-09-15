import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    api_key = os.environ["API_KEY"]
    anthropic_api_key = os.environ["ANTHROPIC_API_KEY"]
    voyage_api_key = os.environ["VOYAGE_API_KEY"]
    qdrant_api_key = os.environ["QDRANT_API_KEY"]
    qdrant_url = os.environ["QDRANT_DB_URL"]
    tavily_api_key = os.environ["TAVILY_API_KEY"]

    chat_model = "claude-sonnet-4-6"  # List of Model ID: https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions
    judge_model = "claude-opus-4-6"
    embed_model = "voyage-4-large"
    rerank_model = "rerank-2.5"
    collection_name = "resume"
    vector_size = 1024
    chunk_size = 500
    chunk_overlap = 50
    max_iterations = 6
    top_k = 5
    input_type_document="document"
    input_type_query="query"


settings = Settings()
