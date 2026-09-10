import os
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("API_KEY")

_api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

def require_api_key(provided: str = Security(_api_key_header)) -> None:
    if provided != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
