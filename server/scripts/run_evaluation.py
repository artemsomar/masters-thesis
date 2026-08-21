import argparse
import asyncio
import sys
from itertools import islice
from pathlib import Path

from app.bootstrap import build_evaluation_container
from app.errors import AppError
from app.infrastructure.llm.client import LlmProviderError

DEFAULT_SIMILARITY_THRESHOLD = 0.8


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate diagram candidates for evaluation dataset cases."
    )
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument(
        "--limit",
        type=_positive_integer,
        help="Maximum number of systems to evaluate; evaluates all systems when omitted.",
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


async def run(
    dataset_path: Path,
    actor_similarity_threshold: float,
    use_case_similarity_threshold: float,
    limit: int | None,
) -> None:
    container = build_evaluation_container(
        actor_similarity_threshold, use_case_similarity_threshold
    )
    cases = container.evaluation_service.load_cases(dataset_path)
    for case in islice(cases, limit):
        result = await container.evaluation_workflow.evaluate_case(case)
        print(result.model_dump_json(by_alias=True))


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
