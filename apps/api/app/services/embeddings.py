"""
Embedding service for semantic matching.

Uses OpenAI text-embedding-3-small with 384 dimensions to match pgvector schema.
Falls back to hash-based projection when OPENAI_API_KEY is not configured.
"""

import hashlib
import math

import httpx

from app.config import settings


EMBEDDING_DIM = 384
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_URL = "https://api.openai.com/v1/embeddings"


class EmbeddingService:

    @staticmethod
    async def embed_text(text: str) -> list[float]:
        """Generate a 384-dimensional embedding from text.

        Uses OpenAI text-embedding-3-small when API key is configured,
        falls back to hash projection otherwise.
        """
        if settings.openai_api_key:
            return await EmbeddingService._embed_openai(text)
        return EmbeddingService._embed_hash(text)

    @staticmethod
    def embed_text_sync(text: str) -> list[float]:
        """Synchronous hash-based fallback for tests and offline use."""
        return EmbeddingService._embed_hash(text)

    @staticmethod
    async def _embed_openai(text: str) -> list[float]:
        text = text[:8000]
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                OPENAI_URL,
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "input": text,
                    "model": OPENAI_EMBEDDING_MODEL,
                    "dimensions": EMBEDDING_DIM,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]

    @staticmethod
    def _embed_hash(text: str) -> list[float]:
        """Deterministic hash-based 384-dim embedding (fallback)."""
        vector = [0.0] * EMBEDDING_DIM
        tokens = text.lower().split()
        if not tokens:
            return vector

        for token in tokens:
            h = hashlib.sha256(token.encode("utf-8")).hexdigest()
            for i in range(EMBEDDING_DIM):
                byte_idx = (i * 2) % len(h)
                val = int(h[byte_idx : byte_idx + 2], 16) / 255.0 - 0.5
                vector[i] += val

        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector

    @staticmethod
    def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
        """Cosine similarity between two vectors (assumed already unit-normalised)."""
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        return max(-1.0, min(1.0, dot))
