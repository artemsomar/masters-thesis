from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha1
import re
from typing import TYPE_CHECKING, TypedDict

import networkx as nx
import numpy as np

from app.modules.diagrams.contracts.graph import (
    RequirementEdgeType,
    RequirementGraph,
    RequirementGraphEdge,
    RequirementGraphNode,
    RequirementNodeType,
)
from app.modules.diagrams.contracts.provenance import Origin, SourceSpan
from app.modules.diagrams.contracts.requirements import RequirementFrame
from app.modules.evaluation.embedding_types import EmbeddingMatrix
from app.modules.evaluation.errors import InvalidEmbeddingResult
from app.modules.evaluation.ports import EmbeddingClient


class InternalNodeAttributes(TypedDict):
    type: RequirementNodeType
    label: str
    frame_ids: list[str]
    spans: list[SourceSpan]
    origins: list[str]
    condition: str | None


class InternalEdgeAttributes(TypedDict):
    type: RequirementEdgeType
    frame_ids: list[str]
    spans: list[SourceSpan]
    origins: list[str]
    similarity_score: float | None


if TYPE_CHECKING:
    InternalGraph = nx.DiGraph[str, InternalNodeAttributes, InternalEdgeAttributes]
else:
    InternalGraph = nx.DiGraph


def normalize_requirement_term(value: str) -> str:
    return " ".join(value.casefold().split())


def _graph_identifier(node_type: RequirementNodeType, value: str) -> str:
    normalized = normalize_requirement_term(value)
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-") or "term"
    digest = sha1(normalized.encode()).hexdigest()[:10]
    return f"{node_type.value}-{slug[:80]}-{digest}"[:100]


def _combined_origin(origins: list[str]) -> Origin:
    if not origins or "unverified" in origins:
        return "unverified"
    derived = sorted(origin for origin in origins if origin.startswith("derived:"))
    return derived[0] if derived else "extracted"


def _unique_spans(spans: list[SourceSpan]) -> list[SourceSpan]:
    seen: set[tuple[int, int, str, str]] = set()
    result: list[SourceSpan] = []
    for span in spans:
        key = (span.start_offset, span.end_offset, span.text, span.origin)
        if key not in seen:
            seen.add(key)
            result.append(span)
    return result


@dataclass(frozen=True, slots=True)
class RequirementGraphSettings:
    similarity_threshold: float = 0.85

    def __post_init__(self) -> None:
        if not 0 <= self.similarity_threshold <= 1:
            raise ValueError("similarity_threshold must be between 0 and 1")


class RequirementGraphBuilder:
    """Builds the requirement graph while keeping NetworkX out of the domain contract."""

    def __init__(
        self,
        embedding_client: EmbeddingClient | None = None,
        settings: RequirementGraphSettings | None = None,
    ) -> None:
        self._embedding_client = embedding_client
        self._settings = settings or RequirementGraphSettings()

    async def build(self, frames: list[RequirementFrame]) -> RequirementGraph:
        graph: InternalGraph = nx.DiGraph()
        for frame in sorted(frames, key=lambda item: item.id):
            requirement_id = _graph_identifier(RequirementNodeType.REQUIREMENT, frame.id)
            graph.add_node(
                requirement_id,
                type=RequirementNodeType.REQUIREMENT,
                label=frame.id,
                frame_ids=[frame.id],
                spans=list(frame.spans),
                origins=[frame.origin],
                condition=frame.condition,
            )
            action_id = self._add_term_node(graph, frame, RequirementNodeType.ACTION, frame.action)
            actor_id = self._add_term_node(graph, frame, RequirementNodeType.ACTOR, frame.actor)
            object_id = self._add_term_node(graph, frame, RequirementNodeType.OBJECT, frame.object)
            if actor_id is not None and action_id is not None:
                self._add_edge(graph, RequirementEdgeType.PERFORMS, actor_id, action_id, frame)
            if action_id is not None and object_id is not None:
                self._add_edge(graph, RequirementEdgeType.TARGETS, action_id, object_id, frame)

        await self._add_similarity_edges(graph)
        return self._to_contract(graph)

    @staticmethod
    def _add_term_node(
        graph: InternalGraph,
        frame: RequirementFrame,
        node_type: RequirementNodeType,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        node_id = _graph_identifier(node_type, value)
        if node_id not in graph:
            graph.add_node(
                node_id,
                type=node_type,
                label=value,
                frame_ids=[frame.id],
                spans=list(frame.spans),
                origins=[frame.origin],
                condition=None,
            )
            return node_id
        node = graph.nodes[node_id]
        node["frame_ids"].append(frame.id)
        node["spans"].extend(frame.spans)
        node["origins"].append(frame.origin)
        return node_id

    @staticmethod
    def _add_edge(
        graph: InternalGraph,
        edge_type: RequirementEdgeType,
        source_id: str,
        target_id: str,
        frame: RequirementFrame,
    ) -> None:
        if graph.has_edge(source_id, target_id):
            edge = graph.edges[source_id, target_id]
            edge["frame_ids"].append(frame.id)
            edge["spans"].extend(frame.spans)
            edge["origins"].append(frame.origin)
            return
        graph.add_edge(
            source_id,
            target_id,
            type=edge_type,
            frame_ids=[frame.id],
            spans=list(frame.spans),
            origins=[frame.origin],
            similarity_score=None,
        )

    async def _add_similarity_edges(self, graph: InternalGraph) -> None:
        if self._embedding_client is None:
            return
        for node_type in (
            RequirementNodeType.ACTOR,
            RequirementNodeType.ACTION,
            RequirementNodeType.OBJECT,
        ):
            node_ids = sorted(
                node_id for node_id, node in graph.nodes.items() if node["type"] is node_type
            )
            if len(node_ids) < 2:
                continue
            vectors = await self._embedding_client.embed(
                [normalize_requirement_term(graph.nodes[node_id]["label"]) for node_id in node_ids]
            )
            similarities = _cosine_similarity(vectors, len(node_ids))
            for row, source_id in enumerate(node_ids):
                for column in range(row + 1, len(node_ids)):
                    score = similarities[row, column]
                    if score < self._settings.similarity_threshold:
                        continue
                    target_id = node_ids[column]
                    graph.add_edge(
                        source_id,
                        target_id,
                        type=RequirementEdgeType.SIMILAR,
                        frame_ids=sorted(
                            set(graph.nodes[source_id]["frame_ids"])
                            | set(graph.nodes[target_id]["frame_ids"])
                        ),
                        spans=_unique_spans(
                            graph.nodes[source_id]["spans"] + graph.nodes[target_id]["spans"]
                        ),
                        origins=graph.nodes[source_id]["origins"]
                        + graph.nodes[target_id]["origins"],
                        similarity_score=float(score),
                    )

    @staticmethod
    def _to_contract(graph: InternalGraph) -> RequirementGraph:
        nodes = [
            RequirementGraphNode(
                id=node_id,
                type=node["type"],
                label=node["label"],
                frame_ids=sorted(set(node["frame_ids"])),
                spans=_unique_spans(node["spans"]),
                origin=_combined_origin(node["origins"]),
                condition=node["condition"],
            )
            for node_id, node in sorted(graph.nodes.items())
        ]
        edges = [
            RequirementGraphEdge(
                type=edge["type"],
                source_id=source_id,
                target_id=target_id,
                frame_ids=sorted(set(edge["frame_ids"])),
                spans=_unique_spans(edge["spans"]),
                origin=_combined_origin(edge["origins"]),
            )
            for source_id, target_id, edge in sorted(graph.edges(data=True))
        ]
        return RequirementGraph(nodes=nodes, edges=edges)


def _cosine_similarity(vectors: EmbeddingMatrix, expected_count: int) -> np.ndarray:
    matrix = np.asarray(vectors, dtype=np.float32)
    if matrix.ndim != 2 or matrix.shape[0] != expected_count or matrix.shape[1] == 0:
        raise InvalidEmbeddingResult()
    norms = np.linalg.norm(matrix, axis=1)
    if np.any(norms == 0):
        raise InvalidEmbeddingResult()
    normalized = matrix / norms[:, np.newaxis]
    return normalized @ normalized.T
