from fastapi import FastAPI
from backend.api.routes import router
from backend.logging_config import setup_logging

setup_logging()
app = FastAPI()
app.include_router(router)