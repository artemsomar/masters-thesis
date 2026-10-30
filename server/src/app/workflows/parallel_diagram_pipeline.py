import asyncio
import re

import structlog
from app.infrastructure.llm.client import StructuredLlmClient
from app.modules.diagrams.enums import ActorType, RelationType
from app.modules.diagrams.parallel_pipeline_prompts import (
    SYSTEM_INSTRUCTION,
    build_actors_prompt,
    build_related_pairs_prompt,
    build_relation_types_prompt,
    build_use_cases_prompt,
)
from app.modules.diagrams.parallel_pipeline_schemas import (
    ActorsOutput,
    RelatedPairsOutput,
    TypedRelationsOutput,
    UseCasesOutput,
)
from app.modules.diagrams.schemas import Actor, Diagram, DiagramRelation, DiagramSystem, UseCase

logger = structlog.get_logger(__name__)


class ParallelDiagramPipeline:
    """Builds a diagram from four independent LLM requests instead of grounded frame extraction."""

    def __init__(self, llm_client: StructuredLlmClient) -> None:
        self._llm_client = llm_client

    async def run(self, description: str, language: str) -> Diagram:
        actors_output, use_cases_output = await asyncio.gather(
            self._llm_client.generate(
                build_actors_prompt(description, language), ActorsOutput, SYSTEM_INSTRUCTION
            ),
            self._llm_client.generate(
                build_use_cases_prompt(description, language), UseCasesOutput, SYSTEM_INSTRUCTION
            ),
        )
        actor_names = [actor.name for actor in actors_output.actors]
        use_case_names = [use_case.name for use_case in use_cases_output.use_cases]
        logger.info(
            "parallel_pipeline_actors_found", actor_count=len(actor_names), actors=actor_names
        )
        logger.info(
            "parallel_pipeline_use_cases_found",
            use_case_count=len(use_case_names),
            use_cases=use_case_names,
        )

        pairs_output = await self._llm_client.generate(
            build_related_pairs_prompt(description, language, actor_names, use_case_names),
            RelatedPairsOutput,
            SYSTEM_INSTRUCTION,
        )
        logger.info(
            "parallel_pipeline_pairs_found",
            pair_count=len(pairs_output.pairs),
            pairs=[(pair.element_a, pair.element_b) for pair in pairs_output.pairs],
        )

        typed_output = await self._llm_client.generate(
            build_relation_types_prompt(
                description, language, actor_names, use_case_names, pairs_output.pairs
            ),
            TypedRelationsOutput,
            SYSTEM_INSTRUCTION,
        )
        logger.info(
            "parallel_pipeline_relations_typed",
            relation_count=len(typed_output.relations),
            relations=[
                (relation.source, relation.type.value, relation.target)
                for relation in typed_output.relations
            ],
        )

        diagram = _assemble_diagram(actors_output, use_cases_output, typed_output)
        logger.info(
            "parallel_pipeline_diagram_assembled",
            actor_count=len(diagram.actors),
            use_case_count=len(diagram.use_cases),
            relation_count=len(diagram.relations),
        )
        return diagram


def _assemble_diagram(
    actors_output: ActorsOutput,
    use_cases_output: UseCasesOutput,
    typed_output: TypedRelationsOutput,
) -> Diagram:
    actors = _deduplicate_by_id(
        [
            Actor(
                id=_identifier(f"actor-{candidate.name}"),
                name=candidate.name,
                type=ActorType.PRIMARY,
                spans=[],
                origin="unverified",
            )
            for candidate in actors_output.actors
        ]
    )
    use_cases = _deduplicate_by_id(
        [
            UseCase(
                id=_identifier(f"use-case-{candidate.name}"),
                name=candidate.name,
                spans=[],
                origin="unverified",
            )
            for candidate in use_cases_output.use_cases
        ]
    )
    id_by_name = {actor.name.casefold(): actor.id for actor in actors}
    id_by_name.update({use_case.name.casefold(): use_case.id for use_case in use_cases})

    relations: dict[tuple[RelationType, str, str], DiagramRelation] = {}
    for relation in typed_output.relations:
        source_id = id_by_name.get(relation.source.casefold())
        target_id = id_by_name.get(relation.target.casefold())
        if source_id is None or target_id is None:
            logger.warning(
                "parallel_pipeline_relation_endpoint_unresolved",
                source=relation.source,
                target=relation.target,
                type=relation.type.value,
                source_resolved=source_id is not None,
                target_resolved=target_id is not None,
            )
            continue
        if source_id == target_id:
            logger.warning(
                "parallel_pipeline_relation_self_loop_dropped",
                element=relation.source,
                type=relation.type.value,
            )
            continue
        key = (relation.type, source_id, target_id)
        relations.setdefault(
            key,
            DiagramRelation(
                type=relation.type,
                source_id=source_id,
                target_id=target_id,
                spans=[],
                origin="unverified",
            ),
        )

    return Diagram(
        schema_version="1.0",
        system=DiagramSystem(id="system", name="System", spans=[], origin="unverified"),
        actors=actors,
        use_cases=use_cases,
        relations=sorted(
            relations.values(), key=lambda item: (item.type.value, item.source_id, item.target_id)
        ),
        assumptions=[],
        warnings=[],
    )


def _deduplicate_by_id(items: list) -> list:
    seen: dict[str, object] = {}
    for item in items:
        seen.setdefault(item.id, item)
    return list(seen.values())


def _identifier(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-") or "element"
    return normalized[:100]
