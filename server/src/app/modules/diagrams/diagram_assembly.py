from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import re

from app.modules.diagrams.contracts.graph import (
    RequirementEdgeType,
    RequirementGraph,
    RequirementGraphEdge,
    RequirementGraphNode,
    RequirementNodeType,
)
from app.modules.diagrams.contracts.provenance import Origin, SourceSpan
from app.modules.diagrams.enums import ActorType, RelationType
from app.modules.diagrams.schemas import Actor, Diagram, DiagramRelation, DiagramSystem, UseCase


@dataclass(frozen=True, slots=True)
class DiagramAssemblySettings:
    system_id: str = "system"
    system_name: str = "System"


class DiagramAssembler:
    """Deterministically projects a requirement graph into a provenance-preserving UML diagram."""

    def __init__(self, settings: DiagramAssemblySettings | None = None) -> None:
        self._settings = settings or DiagramAssemblySettings()

    def assemble(self, graph: RequirementGraph) -> Diagram:
        nodes = {node.id: node for node in graph.nodes}
        target_edges = [edge for edge in graph.edges if edge.type is RequirementEdgeType.TARGETS]
        performs_edges = [edge for edge in graph.edges if edge.type is RequirementEdgeType.PERFORMS]
        use_case_by_pair: dict[tuple[str, str], UseCase] = {}
        use_cases_by_action: dict[str, list[UseCase]] = {}
        for edge in sorted(target_edges, key=_edge_key):
            action, object_node = nodes[edge.source_id], nodes[edge.target_id]
            if (
                action.type is not RequirementNodeType.ACTION
                or object_node.type is not RequirementNodeType.OBJECT
            ):
                continue
            identifier = _identifier(f"use-case-{action.id}-{object_node.id}")
            use_case = use_case_by_pair.setdefault(
                (action.id, object_node.id),
                UseCase(
                    id=identifier,
                    name=f"{action.label} {object_node.label}",
                    spans=_unique_spans(action.spans + object_node.spans),
                    origin=_combined_origin([action.origin, object_node.origin], action.frame_ids),
                ),
            )
            use_cases_by_action.setdefault(action.id, []).append(use_case)

        standalone_use_cases: dict[str, UseCase] = {}
        for edge in sorted(performs_edges, key=_edge_key):
            action = nodes[edge.target_id]
            if action.type is not RequirementNodeType.ACTION or action.id in use_cases_by_action:
                continue
            use_case = standalone_use_cases.setdefault(
                action.id,
                UseCase(
                    id=_identifier(f"use-case-{action.id}"),
                    name=action.label,
                    spans=list(action.spans),
                    origin=action.origin,
                ),
            )
            use_cases_by_action.setdefault(action.id, []).append(use_case)

        actors = [
            Actor(
                id=_identifier(f"actor-{node.id}"),
                name=node.label,
                type=ActorType.PRIMARY,
                spans=list(node.spans),
                origin=node.origin,
            )
            for node in sorted(graph.nodes, key=lambda item: item.id)
            if node.type is RequirementNodeType.ACTOR
        ]
        actor_by_node = {
            node.id: actor
            for node, actor in zip(
                (
                    item
                    for item in sorted(graph.nodes, key=lambda item: item.id)
                    if item.type is RequirementNodeType.ACTOR
                ),
                actors,
                strict=True,
            )
        }
        relations: list[DiagramRelation] = []
        for edge in sorted(graph.edges, key=_edge_key):
            if edge.type is not RequirementEdgeType.PERFORMS:
                continue
            actor = actor_by_node.get(edge.source_id)
            use_cases = use_cases_by_action.get(edge.target_id, [])
            if actor is None:
                continue
            for use_case in use_cases:
                relations.append(
                    DiagramRelation(
                        type=RelationType.ASSOCIATION,
                        source_id=actor.id,
                        target_id=use_case.id,
                        spans=_unique_spans(edge.spans + actor.spans + use_case.spans),
                        origin=_combined_origin(
                            [edge.origin, actor.origin, use_case.origin], _frame_ids(edge, nodes)
                        ),
                    )
                )
        include_use_cases, include_relations = _include_candidates(use_case_by_pair, nodes)
        relations.extend(include_relations)
        relations.extend(_extend_candidates(use_case_by_pair, target_edges, performs_edges, nodes))
        relations = _deduplicate_relations(relations)
        all_spans = _unique_spans([span for node in graph.nodes for span in node.spans])
        return Diagram(
            schema_version="1.0",
            system=DiagramSystem(
                id=self._settings.system_id,
                name=self._settings.system_name,
                spans=all_spans,
                origin=_combined_origin([node.origin for node in graph.nodes], []),
            ),
            actors=actors,
            use_cases=sorted(
                [*use_case_by_pair.values(), *include_use_cases, *standalone_use_cases.values()],
                key=lambda item: item.id,
            ),
            relations=relations,
            assumptions=[],
            warnings=[],
        )


def _identifier(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-") or "element"
    return normalized[:100]


def _include_candidates(
    use_case_by_pair: dict[tuple[str, str], UseCase],
    nodes: dict[str, RequirementGraphNode],
) -> tuple[list[UseCase], list[DiagramRelation]]:
    pairs_by_action: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for pair in use_case_by_pair:
        pairs_by_action[pair[0]].append(pair)
    shared_use_cases: list[UseCase] = []
    relations: list[DiagramRelation] = []
    for action_id, pairs in sorted(pairs_by_action.items()):
        if len({object_id for _, object_id in pairs}) < 2:
            continue
        action = nodes[action_id]
        shared = UseCase(
            id=_identifier(f"include-{action.id}"),
            name=action.label,
            spans=list(action.spans),
            origin=action.origin,
        )
        shared_use_cases.append(shared)
        for pair in sorted(pairs):
            parent = use_case_by_pair[pair]
            relations.append(
                DiagramRelation(
                    type=RelationType.INCLUDE,
                    source_id=parent.id,
                    target_id=shared.id,
                    spans=_unique_spans(parent.spans + shared.spans),
                    origin=_combined_origin([parent.origin, shared.origin], action.frame_ids),
                )
            )
    return shared_use_cases, relations


def _extend_candidates(
    use_case_by_pair: dict[tuple[str, str], UseCase],
    target_edges: list[RequirementGraphEdge],
    performs_edges: list[RequirementGraphEdge],
    nodes: dict[str, RequirementGraphNode],
) -> list[DiagramRelation]:
    condition_by_frame = {
        frame_id: node.condition
        for node in nodes.values()
        if node.type is RequirementNodeType.REQUIREMENT
        for frame_id in node.frame_ids
    }
    frame_ids_by_pair = {
        (edge.source_id, edge.target_id): set(edge.frame_ids)
        for edge in target_edges
        if (edge.source_id, edge.target_id) in use_case_by_pair
    }
    actors_by_action: dict[str, set[str]] = defaultdict(set)
    for edge in performs_edges:
        actors_by_action[edge.target_id].add(edge.source_id)
    relations: list[DiagramRelation] = []
    for source_pair, source in sorted(use_case_by_pair.items()):
        source_action, source_object = source_pair
        if not _is_conditional(source_pair, frame_ids_by_pair, condition_by_frame):
            continue
        candidates = [
            target_pair
            for target_pair in use_case_by_pair
            if target_pair[0] != source_action
            and target_pair[1] == source_object
            and not _is_conditional(target_pair, frame_ids_by_pair, condition_by_frame)
            and actors_by_action[source_action] & actors_by_action[target_pair[0]]
        ]
        if len(candidates) != 1:
            continue
        target = use_case_by_pair[candidates[0]]
        relations.append(
            DiagramRelation(
                type=RelationType.EXTEND,
                source_id=source.id,
                target_id=target.id,
                spans=_unique_spans(source.spans + target.spans),
                origin=_combined_origin(
                    [source.origin, target.origin], sorted(frame_ids_by_pair[source_pair])
                ),
            )
        )
    return relations


def _is_conditional(
    pair: tuple[str, str],
    frame_ids_by_pair: dict[tuple[str, str], set[str]],
    condition_by_frame: dict[str, str | None],
) -> bool:
    return any(condition_by_frame.get(frame_id) for frame_id in frame_ids_by_pair[pair])


def _edge_key(edge: RequirementGraphEdge) -> tuple[str, str, str]:
    return edge.type.value, edge.source_id, edge.target_id


def _frame_ids(edge: RequirementGraphEdge, nodes: dict[str, RequirementGraphNode]) -> list[str]:
    return sorted(
        set(edge.frame_ids)
        | set(nodes[edge.source_id].frame_ids)
        | set(nodes[edge.target_id].frame_ids)
    )


def _combined_origin(origins: list[str], frame_ids: list[str]) -> Origin:
    if not origins or "unverified" in origins:
        return "unverified"
    if "extracted" in origins:
        return "extracted"
    return f"derived:{sorted(frame_ids)[0]}" if frame_ids else "unverified"


def _unique_spans(spans: list[SourceSpan]) -> list[SourceSpan]:
    unique: dict[tuple[int, int, str, str], SourceSpan] = {}
    for span in spans:
        unique[(span.start_offset, span.end_offset, span.text, span.origin)] = span
    return list(unique.values())


def _deduplicate_relations(relations: list[DiagramRelation]) -> list[DiagramRelation]:
    unique: dict[tuple[RelationType, str, str], DiagramRelation] = {}
    for relation in relations:
        unique.setdefault((relation.type, relation.source_id, relation.target_id), relation)
    return sorted(
        unique.values(), key=lambda item: (item.type.value, item.source_id, item.target_id)
    )
