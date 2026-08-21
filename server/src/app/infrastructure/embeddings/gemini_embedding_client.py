import structlog
from google import genai
from google.genai import types

from app.modules.evaluation.errors import InvalidEmbeddingResult

logger = structlog.get_logger(__name__)


class GeminiEmbeddingClient:
    def __init__(self, api_key: str, model: str, dimensions: int) -> None:
        self._api_key = api_key
        self._model = model
        self._dimensions = dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self._api_key or not self._model:
            raise InvalidEmbeddingResult()
        client = genai.Client(api_key=self._api_key)
        try:
            response = await client.aio.models.embed_content(
                model=self._model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=text)],
                    )
                    for text in texts
                ],
                config=types.EmbedContentConfig(
                    task_type="SEMANTIC_SIMILARITY",
                    output_dimensionality=self._dimensions,
                ),
            )
        except Exception as error:
            logger.error(
                "gemini_embedding_request_failed",
                error_type=type(error).__name__,
                provider_error=str(error),
            )
            raise InvalidEmbeddingResult() from error
        finally:
            client.close()
        vectors = [embedding.values or [] for embedding in response.embeddings or []]
        logger.info(
            "gemini_embeddings_received",
            requested_dimensions=self._dimensions,
            vector_count=len(vectors),
            vector_dimensions=[len(vector) for vector in vectors],
        )
        return vectors
