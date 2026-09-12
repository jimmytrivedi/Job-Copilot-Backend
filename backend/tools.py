from backend.schemas import SEARCH_RESUME_SCHEMA, EXTRACT_REQUIREMENTS_SCHEMA, SEARCH_WEB_SCHEMA
import json
import os
from anthropic import Anthropic
from backend.tavily_client import get_web_search_result

_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def search_resume():
    return {
        "name": "search_resume",
        "description": (
            "Search the candidate's resume for content relevant to query. "
            "Returns matching resume passages. Call this to check whether the candidate has experience with a specific skill or requirement."
        ),
        "input_schema": SEARCH_RESUME_SCHEMA,
        "input_examples": [
            {"query": "Kotlin Jetpack Compose MVVM architecture", "top_k": 5},
            {"query": "machine learning TensorFlow on-device ML", "top_k": 3},
            {"query": "CI/CD pipeline unit testing", "top_k": 5}
        ]
    }

def extract_requirements():
    return {
        "name": "extract_requirements",
        "description": (
            "Parse the raw job description into structured requirements. "
            "Call this ONCE at the start with the full JD text. "
            "Returns must_have list, nice_to_have list, and years of experience."
         ),
        "input_schema": EXTRACT_REQUIREMENTS_SCHEMA,
        "input_examples": [
            {
                "jd": "5+ years Android development with Kotlin and Jetpack Compose",
                "must_have": ["Kotlin", "Jetpack Compose", "5+ years Android"],
                "nice_to_have": ["CI/CD", "unit testing"]
            },
            {
                "jd": "Senior iOS developer with Swift and SwiftUI experience",
                "must_have": ["Swift", "SwiftUI", "iOS development"],
                "nice_to_have": ["CoreData", "Combine"]
            }
        ]
    }

def run_extract_requirements(jd: str) -> dict:
    prompt = f"""Extract requirements from this job description. 
Respond with raw JSON only, no prose, no backticks.

Shape:
{{
  "must_have": [<string>, ...],
  "nice_to_have": [<string>, ...],
  "years": <int>
}}

JD:
{jd}
"""
    response = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text
    return json.loads(text)

def search_web():
    return {
        "name": "search_web",
        "description": "Only use this tool, ff any tech is unfamilier",
        "input_schema": SEARCH_WEB_SCHEMA,
        "input_examples": [
            {"query": "meaning of <keyword>"},
            {"query": "meaning of <keyword>"}
        ]
    }

def run_search_web(query: str) -> dict:
    return get_web_search_result(query)