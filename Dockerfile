FROM python:3.14-slim

RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install uv

COPY pyproject.toml ./
RUN uv sync

COPY . .

CMD ["sh", "-c", "uv run uvicorn main:app --host 0.0.0.0 --port $PORT"]
