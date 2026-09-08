# syntax=docker/dockerfile:1

FROM python:3.13-slim AS builder

RUN pip install --no-cache-dir fastembed

ARG EMBED_MODEL_NAME=BAAI/bge-small-zh-v1.5
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='${EMBED_MODEL_NAME}')"

FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-install-project --no-dev

COPY main.py ./

COPY --from=builder /tmp/fastembed_cache /tmp/fastembed_cache

RUN useradd -m appuser && chown -R appuser:appuser /app /tmp/fastembed_cache
USER appuser

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]   
