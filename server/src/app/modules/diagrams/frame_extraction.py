from collections.abc import Iterable

from app.infrastructure.llm.client import InvalidStructuredOutputError, StructuredLlmClient
from app.modules.diagrams.contracts.provenance import validate_source_spans
from app.modules.diagrams.contracts.requirements import (
    FrameExtractionRequest,
    FrameExtractionResult,
    FrameExtractionWarning,
    RequirementFrame,
    RequirementFrameExtractionOutput,
)
from app.modules.diagrams.errors import InvalidFrameExtraction
from app.modules.diagrams.frame_extraction_prompts import (
    PROMPT_VERSION,
    SYSTEM_INSTRUCTION,
    build_frame_extraction_prompt,
)


class FrameExtractionService:
    def __init__(self, llm_client: StructuredLlmClient, max_description_length: int) -> None:
        self._llm_client = llm_client
        self._max_description_length = max_description_length

    async def extract(self, request: FrameExtractionRequest) -> FrameExtractionResult:
        self._validate_request(request)
        output = await self._generate(request)
        invalid_frame_ids = _invalid_frame_ids(request.description, output.frames)
        if invalid_frame_ids:
            output = await self._generate(request, "One or more source spans were not exact.")
            invalid_frame_ids = _invalid_frame_ids(request.description, output.frames)
        return _to_result(output.frames, invalid_frame_ids)

    def _validate_request(self, request: FrameExtractionRequest) -> None:
        if len(request.description) > self._max_description_length:
            raise InvalidFrameExtraction("description_too_long")

    async def _generate(
        self, request: FrameExtractionRequest, retry_reason: str | None = None
    ) -> RequirementFrameExtractionOutput:
        try:
            return await self._llm_client.generate(
                build_frame_extraction_prompt(request, retry_reason),
                RequirementFrameExtractionOutput,
                SYSTEM_INSTRUCTION,
            )
        except InvalidStructuredOutputError as error:
            raise InvalidFrameExtraction("invalid_structured_output") from error


def _invalid_frame_ids(description: str, frames: Iterable[RequirementFrame]) -> set[str]:
    invalid_ids: set[str] = set()
    for frame in frames:
        try:
            validate_source_spans(description, frame.spans)
        except ValueError:
            invalid_ids.add(frame.id)
    return invalid_ids


def _to_result(
    frames: list[RequirementFrame], invalid_frame_ids: set[str]
) -> FrameExtractionResult:
    warnings = [
        FrameExtractionWarning(
            frame_id=frame.id,
            reason="The model returned a source span that does not match the input description.",
        )
        for frame in frames
        if frame.id in invalid_frame_ids
    ]
    verified_frames = [
        (
            frame.model_copy(update={"spans": [], "origin": "unverified"})
            if frame.id in invalid_frame_ids
            else frame
        )
        for frame in frames
    ]
    return FrameExtractionResult(
        frames=verified_frames,
        warnings=warnings,
        prompt_version=PROMPT_VERSION,
    )
