from backend.domain.models import AnalyzeRequest

from backend.services.analyzer import analyze_with_claude
from backend.services.graph import analyze_graph_stream
from backend.services.supervisor import analyze_supervisor_stream

from backend.api.deps import require_api_key
from backend.api.sse import to_sse

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.get("/")
def root():
    return {"message": "Hello World"}

@router.get("/health")
def health():
    return {"message": "Hello World"}

@router.post("/analyze/stream", dependencies=[Depends(require_api_key)])
def analyze_stream(analyzeRequest: AnalyzeRequest):
    generator = analyze_with_claude(f"JD: {analyzeRequest.jd}")
    return StreamingResponse(to_sse(generator), media_type="text/event-stream")

@router.post("/analyze/graph/stream", dependencies=[Depends(require_api_key)])
def analyze_graph_stream_route(analyzeRequest: AnalyzeRequest):
    generator = analyze_graph_stream(f"JD: {analyzeRequest.jd}")
    return StreamingResponse(to_sse(generator), media_type="text/event-stream")

@router.post("/analyze/supervisor/stream", dependencies=[Depends(require_api_key)])
def analyze_supervisor_stream_route(analyzeRequest: AnalyzeRequest):
    generator = analyze_supervisor_stream(f"JD: {analyzeRequest.jd}")
    return StreamingResponse(to_sse(generator), media_type="text/event-stream")