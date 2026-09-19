import json
from backend.domain.errors import AgentLoopExceeded
from typing import Iterator

def to_sse(events: Iterator[dict]) -> Iterator[str]:
    try:
        for event in events:
            yield f"data: {json.dumps(event)}\n\n"
    except AgentLoopExceeded as e:
        yield f"data: {json.dumps({'stage': 'error', 'detail': str(e)})}\n\n"
