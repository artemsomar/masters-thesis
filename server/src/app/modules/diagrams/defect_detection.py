from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from hashlib import sha1
import re

from app.modules.diagrams.contracts.corrections import (
    CorrectionOperation,
    DefectType,
    DetectedDefect,
)
from app.modules.diagrams.contracts.graph import (
    RequirementEdgeType,
    RequirementGraph,
    RequirementNodeType,
)
from app.modules.diagrams.contracts.requirements import RequirementFrame
from app.modules.diagrams.requirement_graph import normalize_requirement_term


@dataclass(frozen=True, slots=True)
class DefectDetectionSettings:
    vague_verbs: frozenset[str] = field(
        default_factory=lambda: frozenset({"handle", "manage", "process", "perform", "work"})
    )
    action_step_verbs: frozenset[str] = field(
        default_factory=lambda: frozenset({"click", "enter", "navigate", "open", "press", "select"})
    )


class RequirementDefectDetector:
    """Produces stable, rule-backed diagnostics; it never proposes a correction."""

    def __init__(self, settings: DefectDetectionSettings | None = None) -> None:
        self._settings = settings or DefectDetectionSettings()

    def detect(
        self, frames: list[RequirementFrame], graph: RequirementGraph
    ) -> list[DetectedDefect]:
        defects = [
            *self._incomplete_frames(frames),
            *self._compound_actions(frames),
            *self._shared_span_compounds(frames),
            *self._vague_verbs(frames),
            *self._inconsistent_terminology(graph),
            *self._action_steps(frames),
        ]
        return sorted(defects, key=lambda defect: defect.id)

    @staticmethod
    def _incomplete_frames(frames: list[RequirementFrame]) -> list[DetectedDefect]:
        defects: list[DetectedDefect] = []
        for frame in sorted(frames, key=lambda item: item.id):
            # `object` is intentionally excluded: a self-contained named capability
            # (e.g. "Register") is a valid action without a target object.
            missing = [name for name in ("actor", "action") if getattr(frame, name) is None]
            if missing:
                defects.append(
                    _defect(
                        f"incomplete-{frame.id}",
                        DefectType.INCOMPLETE_FRAME,
                        [frame.id],
                        f"Frame is missing {', '.join(missing)}; PERFORMS cannot be formed.",
                        CorrectionOperation.RESOLVE,
                    )
                )
        return defects

    @staticmethod
    def _compound_actions(frames: list[RequirementFrame]) -> list[DetectedDefect]:
        defects: list[DetectedDefect] = []
        for frame in sorted(frames, key=lambda item: item.id):
            if frame.action and re.search(r"\b(and|then|or)\b|[,;]", frame.action, re.IGNORECASE):
                defects.append(
                    _defect(
                        f"compound-action-{frame.id}",
                        DefectType.COMPOUND_STATEMENT,
                        [frame.id],
                        f"Action '{frame.action}' contains more than one action marker.",
                        CorrectionOperation.SPLIT,
                    )
                )
        return defects

    @staticmethod
    def _shared_span_compounds(frames: list[RequirementFrame]) -> list[DetectedDefect]:
        frame_ids_by_span: dict[tuple[int, int, str], set[str]] = defaultdict(set)
        for frame in frames:
            for span in frame.spans:
                frame_ids_by_span[(span.start_offset, span.end_offset, span.text)].add(frame.id)
        defects: list[DetectedDefect] = []
        for (_, _, text), frame_ids in sorted(frame_ids_by_span.items()):
            if len(frame_ids) > 1:
                ids = sorted(frame_ids)
                digest = sha1("|".join(ids).encode()).hexdigest()[:10]
                defects.append(
                    _defect(
                        f"compound-span-{digest}",
                        DefectType.COMPOUND_STATEMENT,
                        ids,
                        f"One source span supports multiple frames: '{text}'.",
                        CorrectionOperation.SPLIT,
                    )
                )
        return defects

    def _vague_verbs(self, frames: list[RequirementFrame]) -> list[DetectedDefect]:
        return [
            _defect(
                f"vague-verb-{frame.id}",
                DefectType.VAGUE_VERB,
                [frame.id],
                f"Action '{frame.action}' is in the configured vague-verb glossary.",
                CorrectionOperation.SPECIFY,
            )
            for frame in sorted(frames, key=lambda item: item.id)
            if frame.action
            and normalize_requirement_term(frame.action) in self._settings.vague_verbs
        ]

    @staticmethod
    def _inconsistent_terminology(graph: RequirementGraph) -> list[DetectedDefect]:
        nodes = {node.id: node for node in graph.nodes}
        defects: list[DetectedDefect] = []
        for edge in graph.edges:
            if edge.type is not RequirementEdgeType.SIMILAR:
                continue
            source = nodes[edge.source_id]
            target = nodes[edge.target_id]
            if source.type not in {RequirementNodeType.ACTOR, RequirementNodeType.ACTION}:
                continue
            defects.append(
                _defect(
                    f"terminology-{edge.source_id}-{edge.target_id}",
                    DefectType.INCONSISTENT_TERMINOLOGY,
                    sorted(set(source.frame_ids) | set(target.frame_ids)),
                    f"{source.type.value.title()} labels '{source.label}' and '{target.label}' are similar.",
                    CorrectionOperation.UNIFY,
                    [source.id, target.id],
                )
            )
        return defects

    def _action_steps(self, frames: list[RequirementFrame]) -> list[DetectedDefect]:
        return [
            _defect(
                f"action-step-{frame.id}",
                DefectType.ACTION_STEP,
                [frame.id],
                f"Action '{frame.action}' is a configured scenario-step verb.",
                CorrectionOperation.MERGE_STEPS,
            )
            for frame in sorted(frames, key=lambda item: item.id)
            if frame.action
            and normalize_requirement_term(frame.action) in self._settings.action_step_verbs
        ]


def _defect(
    identifier: str,
    defect_type: DefectType,
    frame_ids: list[str],
    evidence: str,
    operation: CorrectionOperation,
    node_ids: list[str] | None = None,
) -> DetectedDefect:
    return DetectedDefect(
        id=identifier,
        type=defect_type,
        frame_ids=frame_ids,
        node_ids=node_ids or [],
        evidence=evidence,
        assigned_operation=operation,
    )
