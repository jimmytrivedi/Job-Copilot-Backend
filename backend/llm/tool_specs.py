SEARCH_RESUME_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Search query to find relevant resume chunks"
        },
        "top_k": {
            "type": "integer",
            "description": "Number of chunks to retrieve"
        }
    },
    "required": ["query"]
}

EXTRACT_REQUIREMENTS_SCHEMA = {
    "type": "object",
    "properties": {
        "jd": {
            "type": "string",
            "description": "Extracted requirements from the JD"
        },
        "must_have": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Non-negotiable skills from the JD"
        },
        "nice_to_have": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional skills from the JD"
        }
    },
    "required": ["jd"]
}

SEARCH_WEB_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Search query to find relevant meaning"
        }
    },
    "required": ["query"]
}

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