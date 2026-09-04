"""Shared Ollama embedding adapter used by retrieval and verification."""

from __future__ import annotations

import logging
import time

import httpx
from ollama import RequestError, ResponseError

from core.ollama_clients import get_embed_client

logger = logging.getLogger(__name__)

_MAX_EMBED_CHARS = 8192
_MAX_RETRIES = 4
_RETRY_BASE_SEC = 0.75
_RETRY_MAX_SEC = 2.0


def embed_text(model: str, prompt: str) -> list[float]:
    """Return an embedding vector for text, with truncation and transient retries.

    QUALITY: long-function-justification - this adapter keeps the retry loop,
    exception capture, backoff calculation, and final error propagation together
    so callers observe one atomic Ollama embedding operation.
    """
    text = (prompt or "")[:_MAX_EMBED_CHARS]
    client = get_embed_client()
    last_exc: BaseException | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            response = client.embeddings(model=model, prompt=text)
            result: list[float] = response["embedding"]
            return result
        except (
            ResponseError,
            RequestError,
            ConnectionError,
            TimeoutError,
            httpx.RequestError,
            OSError,
        ) as exc:
            last_exc = exc
            logger.warning(
                "ollama_embeddings.attempt_failed",
                extra={"attempt": attempt, "error": str(exc)},
            )
            if attempt >= _MAX_RETRIES - 1:
                break
            delay = min(_RETRY_BASE_SEC * (2**attempt), _RETRY_MAX_SEC)
            time.sleep(delay)
    if last_exc is None:
        raise RuntimeError("embed_text exhausted retries with no captured exception")
    raise last_exc
