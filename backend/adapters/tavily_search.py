from backend.config import settings
from tavily import TavilyClient

client = TavilyClient(
    api_key=settings.tavily_api_key
)

def get_web_search_result(query: str):
    response = client.search(
        query=query,
        search_depth="advanced",
        include_answer=True
    )
    return response["answer"]