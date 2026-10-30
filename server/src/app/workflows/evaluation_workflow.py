from app.modules.diagrams.errors import (
    InvalidDiagram,
    InvalidFrameExtraction,
    InvalidLocalCorrection,
)
from app.modules.diagrams.schemas import Diagram
from app.modules.evaluation.enums import EvaluationRelationType
from app.modules.evaluation.schemas import (
    ComparableDiagram,
    DiagramEvaluationResult,
    EvaluationCase,
    EvaluationNode,
    EvaluationRelation,
)
from app.modules.evaluation.service import EvaluationService
from app.workflows.requirement_diagram_pipeline import RequirementDiagramPipeline


class EvaluationWorkflow:
    def __init__(
        self,
        requirement_pipeline: RequirementDiagramPipeline,
        evaluation_service: EvaluationService,
    ) -> None:
        self._requirement_pipeline = requirement_pipeline
        self._evaluation_service = evaluation_service

    async def evaluate_case(self, case: EvaluationCase) -> DiagramEvaluationResult:
        try:
            pipeline_result = await self._requirement_pipeline.run(case.description, case.language)
        except (InvalidDiagram, InvalidFrameExtraction, InvalidLocalCorrection):
            return DiagramEvaluationResult(
                case_id=case.case_id,
                generated_diagram=None,
                diagram_prompt_version=None,
                uml_validity_score=0,
            )
        initial = pipeline_result.initial
        raw = pipeline_result.assurance.raw.diagram
        final = pipeline_result.assurance.final.diagram
        initial_comparison = await self._evaluation_service.compare(
            case.reference_diagram,
            _to_comparable_diagram(initial),
            system_description=case.description,
        )
        comparison = await self._evaluation_service.compare(
            case.reference_diagram,
            _to_comparable_diagram(raw),
            system_description=case.description,
        )
        return DiagramEvaluationResult(
            case_id=case.case_id,
            generated_diagram=raw,
            initial_diagram=initial,
            final_diagram=final,
            quality_report=pipeline_result.assurance.report,
            pipeline_versions=pipeline_result.assurance.final.pipeline_versions,
            diagram_prompt_version=None,
            uml_validity_score=1,
            actor_score=comparison.actor_matching.score,
            use_case_score=comparison.use_case_matching.score,
            relationship_scores=comparison.relationship_scores,
            initial_actor_score=initial_comparison.actor_matching.score,
            initial_use_case_score=initial_comparison.use_case_matching.score,
            initial_relationship_scores=initial_comparison.relationship_scores,
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
