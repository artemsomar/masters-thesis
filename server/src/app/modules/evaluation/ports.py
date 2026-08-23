from typing import Protocol

from app.modules.evaluation.embedding_types import EmbeddingMatrix


class EmbeddingClient(Protocol):
    async def embed(self, texts: list[str]) -> EmbeddingMatrix: ...
