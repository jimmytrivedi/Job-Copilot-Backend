import anthropic
from backend.config import settings
from langchain_anthropic import ChatAnthropic

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

model = ChatAnthropic(
    model=settings.chat_model,
    api_key=settings.anthropic_api_key
)