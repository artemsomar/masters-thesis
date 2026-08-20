from google import genai
from google.genai import types

from app.modules.evaluation.errors import InvalidEmbeddingResult


class GeminiEmbeddingClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self._api_key or not self._model:
            raise InvalidEmbeddingResult()
        client = genai.Client(api_key=self._api_key)
        try:
            response = await client.aio.models.embed_content(
                model=self._model,
                contents=texts,
                config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
            )
        except Exception as error:
            raise InvalidEmbeddingResult() from error
        finally:
            client.close()
        if response.embeddings is None:
            raise InvalidEmbeddingResult()
        vectors = [embedding.values for embedding in response.embeddings]
        if any(vector is None for vector in vectors):
            raise InvalidEmbeddingResult()
        return [vector for vector in vectors if vector is not None]
