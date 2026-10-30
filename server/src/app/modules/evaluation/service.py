from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from app.modules.evaluation.dataset_reader import EvaluationDatasetReader
from app.modules.evaluation.errors import EvaluationDescriptionTooLong
from app.modules.evaluation.matching import NodeMatching, match_nodes, match_use_cases
from app.modules.evaluation.metrics import score_relations
from app.modules.evaluation.ports import EmbeddingClient
from app.modules.evaluation.schemas import ComparableDiagram, EvaluationCase, RelationshipScores


@dataclass(frozen=True, slots=True)
class EvaluationComparison:
    actor_matching: NodeMatching
    use_case_matching: NodeMatching
    relationship_scores: RelationshipScores


class EvaluationService:
    def __init__(
        self,
        dataset_reader: EvaluationDatasetReader,
        embedding_client: EmbeddingClient,
        max_description_length: int,
        actor_similarity_threshold: float,
        use_case_similarity_threshold: float,
    ) -> None:
        self._dataset_reader = dataset_reader
        self._embedding_client = embedding_client
        self._max_description_length = max_description_length
        self._actor_similarity_threshold = actor_similarity_threshold
        self._use_case_similarity_threshold = use_case_similarity_threshold

    def load_cases(self, path: Path) -> Iterator[EvaluationCase]:
        for case in self._dataset_reader.read(path):
            self._validate_description(case)
            yield case

    def _validate_description(self, case: EvaluationCase) -> None:
        if len(case.description) > self._max_description_length:
            raise EvaluationDescriptionTooLong(case.case_id)

    async def compare(
        self,
        reference: ComparableDiagram,
        generated: ComparableDiagram,
        *,
        system_description: str,
    ) -> EvaluationComparison:
        actor_matching = await match_nodes(
            reference.actors,
            generated.actors,
            self._actor_similarity_threshold,
            self._embedding_client,
        )
        use_case_matching = await match_use_cases(
            reference.use_cases,
            generated.use_cases,
            system_description,
            self._use_case_similarity_threshold,
            self._embedding_client,
        )
        return EvaluationComparison(
            actor_matching=actor_matching,
            use_case_matching=use_case_matching,
            relationship_scores=score_relations(
                reference.relations,
                generated.relations,
                actor_matching.mapping | use_case_matching.mapping,
            ),
        )
