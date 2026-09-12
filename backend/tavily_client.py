from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()

client = TavilyClient(
    api_key=os.environ.get("TAVILY_API_KEY")
)

def get_web_search_result(query: str):
    response = client.search(
        query=query,
        search_depth="advanced",
        include_answer=True
    )

    print(f"Response: {response["answer"]}")
    return response["answer"]

if __name__ == "__main__":
    get_web_search_result("Hello") # Test purpose