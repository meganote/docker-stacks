from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastembed import TextEmbedding
import numpy as np
import logging
import os
import gc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

parallel_threads = int(os.getenv("EMBED_THREADS", str(os.cpu_count())))
logger.info(f"Using parallel={parallel_threads}")
model = TextEmbedding(model_name="BAAI/bge-small-zh-v1.5")
app = FastAPI()


class EmbedRequest(BaseModel):
    input: list[str]

def quantize_to_binary(embedding: np.ndarray) -> list[int]:
    """Convert float embedding to binary (0 or 1)"""
    return (embedding >= 0).astype(np.uint8).tolist()


def get_batch_size(texts):
    MIN_BATCH_SIZE = 5
    MAX_BATCH_SIZE = 30

    MEM_LIMIT_GB = float(os.getenv("MEM_LIMIT_GB", "2"))
    MAX_CHARS_PER_BATCH = int(MEM_LIMIT_GB * 5_000)

    total_chars = sum(len(t) for t in texts)
    avg_chars = total_chars / len(texts) if texts else 0
    batch_size = max(
        MIN_BATCH_SIZE, min(MAX_BATCH_SIZE, int(MAX_CHARS_PER_BATCH / avg_chars))
    )
    return batch_size


def _process_embeddings(texts: list[str], quantize: bool):
    if len(texts) > 100:
        raise HTTPException(400, "Max 100 texts per request")
    if not texts or any(not t.strip() for t in texts):
        raise HTTPException(400, "Empty text not allowed")

    try:
        batch_size = get_batch_size(texts)
        logger.info(f"batch size: {batch_size}")
        embeds = list(model.embed(texts, batch_size=batch_size))

        if quantize:
            result = [quantize_to_binary(e) for e in embeds]
        else:
            result = [e.tolist() for e in embeds]

        return result
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(500, f"Embedding failed: {str(e)}")


@app.post("/v1/embeddings")
def embeddings(req: EmbedRequest):
    embeds = _process_embeddings(req.input, False)
    return {"embeddings": embeds}


@app.post("/v1/embeddings/binary")
def embeddings_binary(req: EmbedRequest):
    embeds = _process_embeddings(req.input, True)
    return {"embeddings": embeds}


@app.get("/health")
def health():
    return {"status": "ok"}
