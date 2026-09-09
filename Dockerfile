FROM python:3.14-slim

RUN apt-get update && apt-get install -y nodejs npm

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

CMD uv run uvicorn main:app --host 0.0.0.0 --port $port