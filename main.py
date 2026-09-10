from fastapi import FastAPI, Depends
from backend.models import Assessment, AnalyzeRequest
from backend.claude_client import analyze_with_claude
from backend.mcp_client import log_application
from backend.auth import require_api_key

app = FastAPI()

@app.get("/")
def root():
    return ({"message": "Hello World"})

@app.get("/health")
def root():
    return {"message": "Hello World"}

@app.post("/analyze", dependencies=[Depends(require_api_key)])
def analyze(analyzeRequest: AnalyzeRequest) -> Assessment:
    result = analyze_with_claude(f"JD: {analyzeRequest.jd}")
    return result

@app.post("/log-application",dependencies=[Depends(require_api_key)])
async def log_app(analyzeRequest: AnalyzeRequest):
    assessment = analyze_with_claude(f"JD: {analyzeRequest.jd}")
    filename = await log_application(analyzeRequest.jd, assessment)
    return {"filename": filename}