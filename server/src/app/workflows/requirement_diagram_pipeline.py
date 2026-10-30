from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import structlog
from app.modules.diagrams.contracts.corrections import ProvenanceDecision
from app.modules.diagrams.contracts.results import (
    DiagramQualityReport,
    PipelineVersions,
    RawDiagram,
)
from app.modules.diagrams.diagram_assembly import DiagramAssembler
from app.modules.diagrams.diagram_assurance import DiagramAssuranceResult, DiagramAssuranceService
from app.modules.diagrams.frame_extraction import FrameExtractionService
from app.modules.diagrams.local_correction import LocalCorrectionService
from app.modules.diagrams.requirement_graph import RequirementGraphBuilder
from app.modules.diagrams.defect_detection import RequirementDefectDetector
from app.modules.diagrams.contracts.requirements import FrameExtractionRequest, RequirementFrame
from app.modules.diagrams.schemas import Diagram

DEFECT_RULES_VERSION = "v1"
ASSURANCE_RULES_VERSION = "v1"
CORRECTION_PASSES = 2

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class RequirementDiagramPipelineResult:
    assurance: DiagramAssuranceResult
    initial: Diagram


class RequirementDiagramPipeline:
    def __init__(
        self,
        frame_extraction_service: FrameExtractionService,
        graph_builder: RequirementGraphBuilder,
        defect_detector: RequirementDefectDetector,
        local_correction_service: LocalCorrectionService,
        diagram_assembler: DiagramAssembler,
        diagram_assurance_service: DiagramAssuranceService,
        embedding_model: str | None,
        similarity_threshold: float,
    ) -> None:
        self._frame_extraction_service = frame_extraction_service
        self._graph_builder = graph_builder
        self._defect_detector = defect_detector
        self._local_correction_service = local_correction_service
        self._diagram_assembler = diagram_assembler
        self._diagram_assurance_service = diagram_assurance_service
        self._embedding_model = embedding_model
        self._similarity_threshold = similarity_threshold

    async def run(
        self,
        description: str,
        language: str,
        report_phase: Callable[[str], Awaitable[None]] | None = None,
    ) -> RequirementDiagramPipelineResult:
        logger.info("requirement_pipeline_started", language=language)
        await _report_phase(report_phase, "extracting_frames")
        extraction = await self._frame_extraction_service.extract(
            FrameExtractionRequest(description=description, language=language)
        )
        frames = extraction.frames
        logger.info(
            "frames_extracted",
            frame_count=len(frames),
            unverified_frame_count=len(extraction.warnings),
            prompt_version=extraction.prompt_version,
        )
        initial_graph = await self._graph_builder.build(frames)
        initial_diagram = self._diagram_assembler.assemble(initial_graph).model_copy(
            update={"warnings": [warning.reason for warning in extraction.warnings]}
        )
        logger.info(
            "initial_diagram_assembled",
            actor_count=len(initial_diagram.actors),
            use_case_count=len(initial_diagram.use_cases),
        )
        decisions: list[ProvenanceDecision] = []
        correction_versions: dict[str, str] = {}
        await _report_phase(report_phase, "analyzing_requirements")
        for pass_number in range(1, CORRECTION_PASSES + 1):
            await _report_phase(report_phase, "correcting_requirements")
            frames, pass_decisions, pass_versions = await self._correct_pass(
                frames, description, pass_number
            )
            decisions.extend(pass_decisions)
            correction_versions.update(pass_versions)
        graph = await self._graph_builder.build(frames)
        remaining_defects = self._defect_detector.detect(frames, graph)
        logger.info(
            "final_requirement_graph_built",
            node_count=len(graph.nodes),
            edge_count=len(graph.edges),
            remaining_defect_count=len(remaining_defects),
        )
        raw = RawDiagram(
            diagram=self._diagram_assembler.assemble(graph).model_copy(
                update={"warnings": [warning.reason for warning in extraction.warnings]}
            ),
            pipeline_versions=PipelineVersions(
                frame_extraction_prompt=extraction.prompt_version,
                local_correction_prompts=correction_versions,
                defect_rules=DEFECT_RULES_VERSION,
                assurance_rules=ASSURANCE_RULES_VERSION,
                embedding_model=self._embedding_model,
                similarity_threshold=self._similarity_threshold,
            ),
        )
        assurance = self._diagram_assurance_service.assure(raw, description)
        logger.info(
            "diagram_assured",
            raw_actor_count=len(raw.diagram.actors),
            raw_use_case_count=len(raw.diagram.use_cases),
            final_actor_count=len(assurance.final.diagram.actors),
            final_use_case_count=len(assurance.final.diagram.use_cases),
            automatic_fix_count=len(assurance.report.automatic_fixes),
            assurance_warning_count=len(assurance.report.assurance_warnings),
        )
        report = assurance.report.model_copy(
            update={
                "remaining_defects": remaining_defects,
                "provenance_decisions": decisions,
            }
        )
        logger.info("requirement_pipeline_completed", remaining_defect_count=len(remaining_defects))
        return RequirementDiagramPipelineResult(
            assurance=DiagramAssuranceResult(
                raw=assurance.raw,
                final=assurance.final,
                report=report,
            ),
            initial=initial_diagram,
        )

    async def _correct_pass(
        self, frames: list[RequirementFrame], description: str, pass_number: int
    ) -> tuple[list[RequirementFrame], list[ProvenanceDecision], dict[str, str]]:
        graph = await self._graph_builder.build(frames)
        defects = self._defect_detector.detect(frames, graph)
        logger.info(
            "requirement_graph_built",
            pass_number=pass_number,
            node_count=len(graph.nodes),
            edge_count=len(graph.edges),
            defect_count=len(defects),
        )
        decisions: list[ProvenanceDecision] = []
        versions: dict[str, str] = {}
        corrected = frames
        for defect in defects:
            logger.info(
                "local_correction_started",
                pass_number=pass_number,
                defect_id=defect.id,
                defect_type=defect.type,
            )
            result = await self._local_correction_service.correct(
                defect, corrected, graph, description
            )
            corrected = _replace_local_frames(corrected, result.frames, defect.frame_ids)
            decisions.append(result.gate_result.decision)
            versions[defect.id] = result.prompt_version
            logger.info(
                "local_correction_completed",
                pass_number=pass_number,
                defect_id=defect.id,
                accepted=result.gate_result.accepted,
            )
        return corrected, decisions, versions


def _replace_local_frames(
    frames: list[RequirementFrame], replacements: list[RequirementFrame], frame_ids: list[str]
) -> list[RequirementFrame]:
    target_ids = set(frame_ids)
    retained = [frame for frame in frames if frame.id not in target_ids]
    return sorted([*retained, *replacements], key=lambda frame: frame.id)


async def _report_phase(report_phase: Callable[[str], Awaitable[None]] | None, phase: str) -> None:
    if report_phase is not None:
        await report_phase(phase)
