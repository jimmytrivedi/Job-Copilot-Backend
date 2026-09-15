from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from backend.domain.models import AnalyzeRequest
from backend.services.analyzer import analyze_with_claude
from backend.api.deps import require_api_key
from backend.api.sse import to_sse

router = APIRouter()

@router.get("/")
def root():
    return {"message": "Hello World"}

@router.get("/health")
def health():
    return {"message": "Hello World"}

# @router.post("/analyze", dependencies=[Depends(require_api_key)])
# def analyze(analyzeRequest: AnalyzeRequest) -> Assessment:
#     result = analyze_with_claude(f"JD: {analyzeRequest.jd}")
#     return result

@router.post("/analyze/stream", dependencies=[Depends(require_api_key)])
def analyze_stream(analyzeRequest: AnalyzeRequest):
    generator = analyze_with_claude(f"JD: {analyzeRequest.jd}")
    return StreamingResponse(to_sse(generator), media_type="text/event-stream")


# @router.post("/log-application",dependencies=[Depends(require_api_key)])
# async def log_app(analyzeRequest: AnalyzeRequest):
#     assessment = analyze_with_claude(f"JD: {analyzeRequest.jd}")
#     filename = await log_application(analyzeRequest.jd, assessment)
#     return {"filename": filename}