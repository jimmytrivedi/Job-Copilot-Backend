import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

JUDGE_PROMPT = """You're a strict evaluator grading an AI's job-fit assessment.

Job Description:
{jd}

AI's Response:
{response}

Grade on this criteria:
1. Did the AI correctly identify the major gaps for this JD?
2. Is the match_score reasonable given the fit (strong-fit = 60-85, mismatch = 0-25, edge = 20-60)?
3. Do the tailored_bullets stay grounded (no invented skills)?


Return raw json only. No markdown, no prose.

{{
"verdict": "PASS" or "FAIL",
"reasoning": "<one sentence explaining why>"
}}
"""

def judge_response(jd: str, response: dict) -> dict:
    prompt = JUDGE_PROMPT.format(jd=jd, response=json.dumps(response, indent=2))
    result = _client.messages.create(
        model="claude-opus-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )

    text = result.content[0].text
    return json.loads(text)