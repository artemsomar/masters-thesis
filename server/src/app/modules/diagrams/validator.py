from app.modules.diagrams.errors import InvalidDiagram
from app.modules.diagrams.schemas import (
    AssociationRelation,
    Diagram,
    ExtendRelation,
    GeneralizationRelation,
    IncludeRelation,
)


def validate_diagram(diagram: Diagram) -> None:
    actor_ids = {actor.id for actor in diagram.actors}
    use_case_ids = {use_case.id for use_case in diagram.use_cases}
    if len(actor_ids) != len(diagram.actors) or len(use_case_ids) != len(diagram.use_cases):
        raise InvalidDiagram()
    if actor_ids & use_case_ids:
        raise InvalidDiagram()
    for relation in diagram.relations:
        _validate_relation(relation, actor_ids, use_case_ids)


def _validate_relation(
    relation: AssociationRelation | IncludeRelation | ExtendRelation | GeneralizationRelation,
    actor_ids: set[str],
    use_case_ids: set[str],
) -> None:
    if isinstance(relation, AssociationRelation):
        if relation.source_id not in actor_ids or relation.target_id not in use_case_ids:
            raise InvalidDiagram()
        return
    if isinstance(relation, (IncludeRelation, ExtendRelation)):
        if relation.source_id not in use_case_ids or relation.target_id not in use_case_ids:
            raise InvalidDiagram()
        if relation.source_id == relation.target_id:
            raise InvalidDiagram()
        return
    if (relation.source_id in actor_ids and relation.target_id in actor_ids) or (
        relation.source_id in use_case_ids and relation.target_id in use_case_ids
    ):
        if relation.source_id != relation.target_id:
            return
    raise InvalidDiagram()
