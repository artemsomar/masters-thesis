from collections.abc import Iterator
from pathlib import Path

from pydantic import ValidationError

from app.modules.evaluation.errors import EvaluationDatasetNotFound, InvalidEvaluationDataset
from app.modules.evaluation.schemas import (
    ComparableDiagram,
    DatasetDiagram,
    EvaluationCase,
    EvaluationNode,
    EvaluationRelation,
)

DESCRIPTION_FILENAME = "description.txt"
DIAGRAM_FILENAME = "diagram.json"
DATASET_LANGUAGE = "en"


class EvaluationDatasetReader:
    def read(self, path: Path) -> Iterator[EvaluationCase]:
        if not path.is_dir():
            raise EvaluationDatasetNotFound(path)
        for case_directory in sorted(
            candidate for candidate in path.iterdir() if candidate.is_dir()
        ):
            yield self._read_case(case_directory)

    def _read_case(self, case_directory: Path) -> EvaluationCase:
        description_path = case_directory / DESCRIPTION_FILENAME
        diagram_path = case_directory / DIAGRAM_FILENAME
        if not description_path.is_file() or not diagram_path.is_file():
            raise InvalidEvaluationDataset(case_directory, "required files are missing")
        try:
            description = description_path.read_text(encoding="utf-8").strip()
            diagram = DatasetDiagram.model_validate_json(diagram_path.read_text(encoding="utf-8"))
        except (OSError, ValidationError) as error:
            raise InvalidEvaluationDataset(
                case_directory, "files cannot be read or validated"
            ) from error
        if not description:
            raise InvalidEvaluationDataset(description_path, "description is empty")
        reference_diagram = _to_comparable_diagram(diagram)
        _validate_relation_endpoints(reference_diagram, diagram_path)
        return EvaluationCase(
            case_id=case_directory.name,
            description=description,
            language=DATASET_LANGUAGE,
            reference_diagram=reference_diagram,
        )


def _to_comparable_diagram(diagram: DatasetDiagram) -> ComparableDiagram:
    return ComparableDiagram(
        actors=[EvaluationNode(id=actor.id, name=actor.name) for actor in diagram.actors],
        use_cases=[
            EvaluationNode(id=use_case.id, name=use_case.name) for use_case in diagram.use_cases
        ],
        relations=[
            EvaluationRelation(
                type=relation.type,
                source_id=relation.source,
                target_id=relation.target,
            )
            for relation in diagram.relationships
        ],
    )


def _validate_relation_endpoints(diagram: ComparableDiagram, path: Path) -> None:
    node_ids = {node.id for node in diagram.actors} | {node.id for node in diagram.use_cases}
    if any(
        relation.source_id not in node_ids or relation.target_id not in node_ids
        for relation in diagram.relations
    ):
        raise InvalidEvaluationDataset(path, "a relation references an unknown node")
