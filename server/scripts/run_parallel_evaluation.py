import argparse
import asyncio
import json
import sys
from itertools import islice
from pathlib import Path

from app.config import get_settings
from app.errors import AppError
from app.infrastructure.embeddings.gemini_embedding_client import GeminiEmbeddingClient
from app.infrastructure.llm.client import LlmProviderError
from app.infrastructure.llm.gemini_structured_client import GeminiStructuredOutputClient
from app.modules.diagrams.schemas import Diagram
from app.modules.evaluation.dataset_reader import EvaluationDatasetReader
from app.modules.evaluation.enums import EvaluationRelationType
from app.modules.evaluation.schemas import ComparableDiagram, EvaluationNode, EvaluationRelation
from app.modules.evaluation.service import EvaluationService
from app.workflows.parallel_diagram_pipeline import ParallelDiagramPipeline

DEFAULT_SIMILARITY_THRESHOLD = 0.8


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate the four-request parallel diagram pipeline against a dataset."
    )
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument(
        "--limit",
        type=_positive_integer,
        help="Maximum number of dataset cases to evaluate; evaluates all cases when omitted.",
    )
    parser.add_argument(
        "--actor-similarity-threshold",
        default=DEFAULT_SIMILARITY_THRESHOLD,
        type=_similarity_threshold,
    )
    parser.add_argument(
        "--use-case-similarity-threshold",
        default=DEFAULT_SIMILARITY_THRESHOLD,
        type=_similarity_threshold,
    )
    return parser.parse_args()


def _similarity_threshold(value: str) -> float:
    threshold = float(value)
    if not 0 <= threshold <= 1:
        raise argparse.ArgumentTypeError("similarity threshold must be between 0 and 1")
    return threshold


def _positive_integer(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("limit must be at least 1")
    return number


def _to_comparable_diagram(diagram: Diagram) -> ComparableDiagram:
    return ComparableDiagram(
        actors=[EvaluationNode(id=actor.id, name=actor.name) for actor in diagram.actors],
        use_cases=[
            EvaluationNode(id=use_case.id, name=use_case.name) for use_case in diagram.use_cases
        ],
        relations=[
            EvaluationRelation(
                type=EvaluationRelationType(relation.type),
                source_id=relation.source_id,
                target_id=relation.target_id,
            )
            for relation in diagram.relations
        ],
    )


async def run(
    dataset_path: Path,
    actor_similarity_threshold: float,
    use_case_similarity_threshold: float,
    limit: int | None,
) -> None:
    settings = get_settings()
    llm_client = GeminiStructuredOutputClient(settings.gemini_api_key, settings.gemini_model)
    embedding_client = GeminiEmbeddingClient(
        settings.gemini_api_key,
        settings.gemini_embedding_model,
        settings.gemini_embedding_dimensions,
    )
    pipeline = ParallelDiagramPipeline(llm_client)
    evaluation_service = EvaluationService(
        EvaluationDatasetReader(),
        embedding_client,
        settings.max_description_length,
        actor_similarity_threshold,
        use_case_similarity_threshold,
    )
    cases = evaluation_service.load_cases(dataset_path)
    for case in islice(cases, limit):
        diagram = await pipeline.run(case.description, case.language)
        comparison = await evaluation_service.compare(
            case.reference_diagram, _to_comparable_diagram(diagram)
        )
        result = {
            "caseId": case.case_id,
            "actors": [actor.name for actor in diagram.actors],
            "useCases": [use_case.name for use_case in diagram.use_cases],
            "relationCount": len(diagram.relations),
            "actorScore": comparison.actor_matching.score.model_dump(),
            "useCaseScore": comparison.use_case_matching.score.model_dump(),
            "relationshipScores": comparison.relationship_scores.model_dump(),
        }
        print(json.dumps(result))


def main() -> int:
    arguments = parse_arguments()
    try:
        asyncio.run(
            run(
                arguments.dataset,
                arguments.actor_similarity_threshold,
                arguments.use_case_similarity_threshold,
                arguments.limit,
            )
        )
    except AppError as error:
        print(error.message, file=sys.stderr)
        return 1
    except LlmProviderError:
        print("The LLM provider could not process the evaluation run", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
