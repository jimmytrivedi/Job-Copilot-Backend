from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    jd: str

class Assessment(BaseModel):
    match_score: int
    strengths: list[str]
    gaps: list[str]
    tailored_bullets: list[str]
    verdict: str