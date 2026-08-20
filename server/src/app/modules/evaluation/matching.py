from dataclasses import dataclass

import faiss
import numpy as np

from app.modules.evaluation.errors import InvalidEmbeddingResult
from app.modules.evaluation.hungarian import maximum_weight_assignment
from app.modules.evaluation.metrics import build_f1_score
from app.modules.evaluation.ports import EmbeddingClient
from app.modules.evaluation.schemas import EvaluationNode, F1Score


@dataclass(frozen=True, slots=True)
class NodeMatching:
    mapping: dict[str, str]
    score: F1Score


async def match_nodes(
    reference: list[EvaluationNode],
    generated: list[EvaluationNode],
    similarity_threshold: float,
    embedding_client: EmbeddingClient,
) -> NodeMatching:
    if not reference or not generated:
        return NodeMatching({}, build_f1_score(0, len(reference), len(generated)))
    vectors = await embedding_client.embed(
        [node.name for node in reference] + [node.name for node in generated]
    )
    if len(vectors) != len(reference) + len(generated):
        raise InvalidEmbeddingResult()
    reference_vectors = vectors[: len(reference)]
    generated_vectors = vectors[len(reference) :]
    similarities = _similarity_matrix(reference_vectors, generated_vectors)
    assignments = maximum_weight_assignment(similarities)
    mapping = {
        reference[row_index].id: generated[column_index].id
        for row_index, column_index in assignments
        if similarities[row_index][column_index] >= similarity_threshold
    }
    return NodeMatching(mapping, build_f1_score(len(mapping), len(reference), len(generated)))


def _similarity_matrix(
    reference_vectors: list[list[float]], generated_vectors: list[list[float]]
) -> list[list[float]]:
    reference_matrix = np.asarray(reference_vectors, dtype=np.float32)
    generated_matrix = np.asarray(generated_vectors, dtype=np.float32)
    if (
        reference_matrix.ndim != 2
        or generated_matrix.ndim != 2
        or reference_matrix.shape[1] != generated_matrix.shape[1]
        or np.any(np.linalg.norm(reference_matrix, axis=1) == 0)
        or np.any(np.linalg.norm(generated_matrix, axis=1) == 0)
    ):
        raise InvalidEmbeddingResult()
    faiss.normalize_L2(reference_matrix)
    faiss.normalize_L2(generated_matrix)
    index = faiss.IndexFlatIP(generated_matrix.shape[1])
    index.add(generated_matrix)
    scores, indices = index.search(reference_matrix, len(generated_vectors))
    if np.any(indices < 0):
        raise InvalidEmbeddingResult()
    similarities = np.empty((len(reference_vectors), len(generated_vectors)), dtype=np.float32)
    for row_index, (row_scores, row_indices) in enumerate(zip(scores, indices, strict=True)):
        similarities[row_index, row_indices] = row_scores
    return similarities.tolist()
