from app.modules.diagrams.errors import InvalidDiagram
from app.modules.diagrams.prompts import PROMPT_VERSION as DIAGRAM_PROMPT_VERSION
from app.modules.diagrams.schemas import Diagram, DiagramGenerationRequest
from app.modules.diagrams.service import DiagramService
from app.modules.evaluation.enums import EvaluationRelationType
from app.modules.evaluation.schemas import (
    ComparableDiagram,
    DiagramEvaluationResult,
    EvaluationCase,
    EvaluationNode,
    EvaluationRelation,
)
from app.modules.evaluation.service import EvaluationService

NO_CLARIFICATION_CONTEXT = "No clarification history."


class EvaluationWorkflow:
    def __init__(
        self, diagram_service: DiagramService, evaluation_service: EvaluationService
    ) -> None:
        self._diagram_service = diagram_service
        self._evaluation_service = evaluation_service

    async def evaluate_case(self, case: EvaluationCase) -> DiagramEvaluationResult:
        try:
            generated = await self._diagram_service.generate(
                DiagramGenerationRequest(
                    description=case.description,
                    language=case.language,
                    clarification_context=NO_CLARIFICATION_CONTEXT,
                )
            )
        except InvalidDiagram:
            return DiagramEvaluationResult(
                case_id=case.case_id,
                generated_diagram=None,
                diagram_prompt_version=DIAGRAM_PROMPT_VERSION,
                uml_validity_score=0,
            )
        actor_matching, use_case_matching, relationship_scores = (
            await self._evaluation_service.compare(
                case.reference_diagram, _to_comparable_diagram(generated)
            )
        )
        return DiagramEvaluationResult(
            case_id=case.case_id,
            generated_diagram=generated.model_dump(by_alias=True),
            diagram_prompt_version=DIAGRAM_PROMPT_VERSION,
            uml_validity_score=1,
            actor_score=actor_matching.score,
            use_case_score=use_case_matching.score,
            relationship_scores=relationship_scores,
        )


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
