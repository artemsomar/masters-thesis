from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
from typing import TypeVar

from app.modules.diagrams.contracts.results import (
    AutomaticDiagramFix,
    DiagramAssuranceWarning,
    DiagramQualityReport,
    FinalDiagram,
    RawDiagram,
    UnverifiedDiagramElement,
)
from app.modules.diagrams.enums import RelationType
from app.modules.diagrams.schemas import Actor, Diagram, DiagramRelation, UseCase

DiagramElement = TypeVar("DiagramElement", Actor, UseCase)


@dataclass(frozen=True, slots=True)
class DiagramAssuranceResult:
    raw: RawDiagram
    final: FinalDiagram
    report: DiagramQualityReport


class DiagramAssuranceService:
    """Generator-agnostic deterministic UML assurance; it never manufactures provenance."""

    def assure(self, raw: RawDiagram, description: str) -> DiagramAssuranceResult:
        del description  # Reserved for evidence-based optional anti-pattern merges.
        diagram = raw.diagram.model_copy(deep=True)
        fixes: list[AutomaticDiagramFix] = []
        warnings: list[DiagramAssuranceWarning] = []
        unverified = _unverified_elements(diagram)

        diagram.relations = self._drop_invalid_endpoints(diagram, fixes, warnings)
        diagram.relations = self._break_include_cycles(diagram, fixes, warnings)
        self._merge_verified_duplicate_names(diagram, fixes, warnings)
        self._remove_verified_orphans(diagram, fixes, warnings)
        self._mark_antipatterns(diagram, warnings)
        diagram.warnings = sorted(
            {*diagram.warnings, *(warning.description for warning in warnings)}
        )
        report = DiagramQualityReport(
            automatic_fixes=fixes,
            unverified_elements=unverified,
            assurance_warnings=warnings,
        )
        return DiagramAssuranceResult(
            raw=raw,
            final=FinalDiagram(diagram=diagram, pipeline_versions=raw.pipeline_versions),
            report=report,
        )

    @staticmethod
    def _drop_invalid_endpoints(
        diagram: Diagram,
        fixes: list[AutomaticDiagramFix],
        warnings: list[DiagramAssuranceWarning],
    ) -> list[DiagramRelation]:
        actor_ids = {actor.id for actor in diagram.actors}
        use_case_ids = {use_case.id for use_case in diagram.use_cases}
        retained: list[DiagramRelation] = []
        for relation in diagram.relations:
            valid = (
                (
                    relation.type is RelationType.ASSOCIATION
                    and relation.source_id in actor_ids
                    and relation.target_id in use_case_ids
                )
                or (
                    relation.type in {RelationType.INCLUDE, RelationType.EXTEND}
                    and relation.source_id in use_case_ids
                    and relation.target_id in use_case_ids
                    and relation.source_id != relation.target_id
                )
                or (
                    relation.type is RelationType.GENERALIZATION
                    and relation.source_id != relation.target_id
                    and (
                        (relation.source_id in actor_ids and relation.target_id in actor_ids)
                        or (
                            relation.source_id in use_case_ids
                            and relation.target_id in use_case_ids
                        )
                    )
                )
            )
            if valid:
                retained.append(relation)
            elif relation.origin == "unverified":
                warnings.append(
                    _warning(
                        "invalid_relation",
                        "Unverified relation has invalid UML endpoints and was retained.",
                        [relation.source_id, relation.target_id],
                    )
                )
                retained.append(relation)
            else:
                fixes.append(
                    _fix(
                        "invalid_relation",
                        "Removed relation with invalid UML endpoints.",
                        [relation.source_id, relation.target_id],
                    )
                )
        return retained

    @staticmethod
    def _break_include_cycles(
        diagram: Diagram,
        fixes: list[AutomaticDiagramFix],
        warnings: list[DiagramAssuranceWarning],
    ) -> list[DiagramRelation]:
        retained: list[DiagramRelation] = []
        adjacency: dict[str, set[str]] = {}
        for relation in sorted(
            diagram.relations, key=lambda item: (item.source_id, item.target_id, item.type.value)
        ):
            if relation.type is not RelationType.INCLUDE:
                retained.append(relation)
                continue
            if _has_path(adjacency, relation.target_id, relation.source_id):
                if relation.origin == "unverified":
                    warnings.append(
                        _warning(
                            "include_cycle",
                            "Unverified include relation closes a cycle and was retained.",
                            [relation.source_id, relation.target_id],
                        )
                    )
                    retained.append(relation)
                else:
                    fixes.append(
                        _fix(
                            "include_cycle",
                            "Removed include relation that closes a cycle.",
                            [relation.source_id, relation.target_id],
                        )
                    )
                continue
            adjacency.setdefault(relation.source_id, set()).add(relation.target_id)
            retained.append(relation)
        return retained

    @staticmethod
    def _merge_verified_duplicate_names(
        diagram: Diagram,
        fixes: list[AutomaticDiagramFix],
        warnings: list[DiagramAssuranceWarning],
    ) -> None:
        diagram.actors, actor_replacements = _merge_duplicate_items(diagram.actors, fixes, warnings)
        diagram.use_cases, use_case_replacements = _merge_duplicate_items(
            diagram.use_cases, fixes, warnings
        )
        replacements = actor_replacements | use_case_replacements
        if replacements:
            diagram.relations = [
                relation.model_copy(
                    update={
                        "source_id": replacements.get(relation.source_id, relation.source_id),
                        "target_id": replacements.get(relation.target_id, relation.target_id),
                    }
                )
                for relation in diagram.relations
            ]

    @staticmethod
    def _remove_verified_orphans(
        diagram: Diagram,
        fixes: list[AutomaticDiagramFix],
        warnings: list[DiagramAssuranceWarning],
    ) -> None:
        connected_use_cases = {
            identifier
            for relation in diagram.relations
            for identifier in (relation.source_id, relation.target_id)
            if relation.type
            in {RelationType.ASSOCIATION, RelationType.INCLUDE, RelationType.EXTEND}
        }
        for use_case in list(diagram.use_cases):
            if use_case.id in connected_use_cases:
                continue
            if use_case.origin == "unverified":
                warnings.append(
                    _warning(
                        "use_case_without_actor",
                        "Unverified use case has no actor association and was retained.",
                        [use_case.id],
                    )
                )
                continue
            diagram.use_cases.remove(use_case)
            diagram.relations = [
                relation
                for relation in diagram.relations
                if use_case.id not in {relation.source_id, relation.target_id}
            ]
            fixes.append(
                _fix(
                    "use_case_without_actor",
                    "Removed verified use case without an actor association.",
                    [use_case.id],
                )
            )
        connected = {
            identifier
            for relation in diagram.relations
            for identifier in (relation.source_id, relation.target_id)
        }
        for actor in list(diagram.actors):
            if actor.id in connected:
                continue
            if actor.origin == "unverified":
                warnings.append(
                    _warning("isolated_node", "Unverified isolated actor was retained.", [actor.id])
                )
                continue
            diagram.actors.remove(actor)
            fixes.append(_fix("isolated_node", "Removed verified isolated actor.", [actor.id]))

    @staticmethod
    def _mark_antipatterns(diagram: Diagram, warnings: list[DiagramAssuranceWarning]) -> None:
        crud = {"create", "read", "update", "delete"}
        for use_case in diagram.use_cases:
            verb = use_case.name.casefold().split(maxsplit=1)[0]
            if verb in crud:
                warnings.append(
                    _warning(
                        "excessive_crud",
                        "CRUD-level use case is retained as an anti-pattern warning.",
                        [use_case.id],
                    )
                )
            if verb in {"click", "enter", "navigate", "open", "press", "select"}:
                warnings.append(
                    _warning(
                        "action_step",
                        "Scenario-step use case is retained as an anti-pattern warning.",
                        [use_case.id],
                    )
                )


def _has_path(adjacency: dict[str, set[str]], start: str, target: str) -> bool:
    pending = [start]
    visited: set[str] = set()
    while pending:
        node = pending.pop()
        if node == target:
            return True
        if node in visited:
            continue
        visited.add(node)
        pending.extend(adjacency.get(node, set()) - visited)
    return False


def _unverified_elements(diagram: Diagram) -> list[UnverifiedDiagramElement]:
    result: list[UnverifiedDiagramElement] = []
    if diagram.system.origin == "unverified":
        result.append(_unverified("system", diagram.system.id))
    result.extend(
        _unverified("actor", item.id) for item in diagram.actors if item.origin == "unverified"
    )
    result.extend(
        _unverified("use_case", item.id)
        for item in diagram.use_cases
        if item.origin == "unverified"
    )
    result.extend(
        _unverified("relation", _relation_identifier(item))
        for item in diagram.relations
        if item.origin == "unverified"
    )
    return result


def _merge_duplicate_items(
    items: list[DiagramElement],
    fixes: list[AutomaticDiagramFix],
    warnings: list[DiagramAssuranceWarning],
) -> tuple[list[DiagramElement], dict[str, str]]:
    canonical: dict[str, DiagramElement] = {}
    replacements: dict[str, str] = {}
    retained: list[DiagramElement] = []
    for item in items:
        key = " ".join(item.name.casefold().split())
        existing = canonical.get(key)
        if existing is None:
            canonical[key] = item
            retained.append(item)
        elif item.origin == "unverified" or existing.origin == "unverified":
            warnings.append(
                _warning(
                    "duplicate_name",
                    "Duplicate name contains an unverified element and was retained.",
                    [existing.id, item.id],
                )
            )
            retained.append(item)
        else:
            replacements[item.id] = existing.id
            fixes.append(
                _fix(
                    "duplicate_name",
                    "Merged duplicate verified UML element names.",
                    [existing.id, item.id],
                )
            )
    return retained, replacements


def _relation_identifier(item: DiagramRelation) -> str:
    digest = sha1(f"{item.source_id}-{item.type.value}-{item.target_id}".encode()).hexdigest()[:8]
    return f"{item.source_id[:35]}-{item.type.value}-{item.target_id[:35]}-{digest}"


def _unverified(kind: str, identifier: str) -> UnverifiedDiagramElement:
    return UnverifiedDiagramElement(
        kind=kind,
        element_id=identifier,
        reason="Element has no confirmed source span.",
    )


def _fix(rule: str, description: str, identifiers: list[str]) -> AutomaticDiagramFix:
    return AutomaticDiagramFix(rule=rule, description=description, affected_element_ids=identifiers)


def _warning(rule: str, description: str, identifiers: list[str]) -> DiagramAssuranceWarning:
    return DiagramAssuranceWarning(
        rule=rule, description=description, affected_element_ids=identifiers
    )
