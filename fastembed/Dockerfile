from python:3.13-slim

RUN pip install --no-cache-dir fastembed
RUN python -c "from fastembed import TextEmbedding;TextEmbedding(model_name='BAAI/bge-small-zh-v1.5')"
