from backend.config import settings

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY = settings.api_key

_api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

def require_api_key(provided: str = Security(_api_key_header)) -> None:
    if provided != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
