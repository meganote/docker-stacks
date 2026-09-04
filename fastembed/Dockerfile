# syntax=docker/dockerfile:1

FROM python:3.13-slim AS model-fetcher

RUN pip install --no-cache-dir fastembed

# 预下载模型到默认缓存目录 /tmp/fastembed_cache
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='BAAI/bge-small-zh-v1.5')"

FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-install-project --no-dev

COPY main.py ./

COPY --from=model-fetcher /tmp/fastembed_cache /tmp/fastembed_cache

RUN useradd -m appuser && chown -R appuser:appuser /app /tmp/fastembed_cache
USER appuser

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]   
