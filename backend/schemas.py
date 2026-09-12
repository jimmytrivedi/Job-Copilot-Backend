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