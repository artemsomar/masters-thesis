from collections import Counter

from app.modules.evaluation.enums import EvaluationRelationType
from app.modules.evaluation.schemas import F1Score, EvaluationRelation, RelationshipScores


def build_f1_score(true_positives: int, reference_total: int, generated_total: int) -> F1Score:
    precision = _ratio(true_positives, generated_total)
    recall = _ratio(true_positives, reference_total)
    if precision + recall == 0:
        return F1Score(precision=precision, recall=recall, f1=0)
    return F1Score(
        precision=precision, recall=recall, f1=2 * precision * recall / (precision + recall)
    )


def score_relations(
    reference: list[EvaluationRelation],
    generated: list[EvaluationRelation],
    node_mapping: dict[str, str],
) -> RelationshipScores:
    return RelationshipScores(
        overall=_score_relation_group(reference, generated, node_mapping),
        association=_score_relation_group(
            reference, generated, node_mapping, EvaluationRelationType.ASSOCIATION
        ),
        include=_score_relation_group(
            reference, generated, node_mapping, EvaluationRelationType.INCLUDE
        ),
        extend=_score_relation_group(
            reference, generated, node_mapping, EvaluationRelationType.EXTEND
        ),
        generalization=_score_relation_group(
            reference, generated, node_mapping, EvaluationRelationType.GENERALIZATION
        ),
    )


def _score_relation_group(
    reference: list[EvaluationRelation],
    generated: list[EvaluationRelation],
    node_mapping: dict[str, str],
    relation_type: EvaluationRelationType | None = None,
) -> F1Score:
    reference_group = _filter_relations(reference, relation_type)
    generated_group = _filter_relations(generated, relation_type)
    generated_counts = Counter(_relation_key(relation) for relation in generated_group)
    true_positives = 0
    for relation in reference_group:
        mapped_relation = _map_relation(relation, node_mapping)
        if mapped_relation is not None and generated_counts[mapped_relation] > 0:
            generated_counts[mapped_relation] -= 1
            true_positives += 1
    return build_f1_score(true_positives, len(reference_group), len(generated_group))


def _filter_relations(
    relations: list[EvaluationRelation], relation_type: EvaluationRelationType | None
) -> list[EvaluationRelation]:
    if relation_type is None:
        return relations
    return [relation for relation in relations if relation.type is relation_type]


def _map_relation(
    relation: EvaluationRelation, node_mapping: dict[str, str]
) -> tuple[EvaluationRelationType, str, str] | None:
    source_id = node_mapping.get(relation.source_id)
    target_id = node_mapping.get(relation.target_id)
    if source_id is None or target_id is None:
        return None
    return relation.type, source_id, target_id


def _relation_key(relation: EvaluationRelation) -> tuple[EvaluationRelationType, str, str]:
    return relation.type, relation.source_id, relation.target_id


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return numerator / denominator
