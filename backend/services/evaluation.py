import json
from backend.config import settings
from backend.adapters.anthropic_llm import client
from anthropic.types import MessageParam
from backend.llm.prompts import JUDGE_PROMPT, RATE_CHUNK_PROMPT
import logging

logger = logging.getLogger(__name__)

def judge_response(jd: str, response: dict) -> dict:
    prompt = JUDGE_PROMPT.format(jd=jd, response=json.dumps(response, indent=2))
    messages: list[MessageParam] = [{"role": "user", "content": prompt}]
    result = client.messages.create(
        model=settings.judge_model,
        max_tokens=256,
        messages=messages
    )

    text = result.content[0].text
    return json.loads(text)

def rate_chunks(query: str, chunks: dict) -> bool:
    prompt = RATE_CHUNK_PROMPT.format(query=query, response=json.dumps(chunks, indent=2))
    messages: list[MessageParam] = [{"role": "user", "content": prompt}]
    result = client.messages.create(
        model=settings.judge_model_opus_4_7,
        max_tokens=256,
        messages=messages
    )

    text = json.loads(result.content[0].text)
    passed = text['sufficient'] == True
    return passed
