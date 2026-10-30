import asyncio
from collections.abc import Sequence
from typing import cast

import pytest
from pydantic import BaseModel

from app.infrastructure.llm.client import InvalidStructuredOutputError, ResponseModel
from app.modules.diagrams.contracts.provenance import SourceSpan
from app.modules.diagrams.contracts.requirements import (
    FrameExtractionRequest,
    RequirementFrame,
    RequirementFrameExtractionOutput,
)
from app.modules.diagrams.errors import InvalidFrameExtraction
from app.modules.diagrams.frame_extraction import FrameExtractionService


class SequentialStructuredLlmClient:
    def __init__(self, results: Sequence[BaseModel | Exception]) -> None:
        self._results = iter(results)
        self.calls: list[tuple[str, type[BaseModel], str]] = []

    async def generate(
        self,
        prompt: str,
        response_schema: type[ResponseModel],
        system_instruction: str,
    ) -> ResponseModel:
        self.calls.append((prompt, response_schema, system_instruction))
        result = next(self._results)
        if isinstance(result, Exception):
            raise result
        return cast(ResponseModel, result)


def test_extraction_retries_once_when_a_source_span_is_invalid() -> None:
    description = "Customer books a service."
    client = SequentialStructuredLlmClient(
        [_output(_frame(description, "Client")), _output(_frame(description, "Customer"))]
    )

    result = asyncio.run(
        FrameExtractionService(client, max_description_length=100).extract(
            FrameExtractionRequest(description=description, language="en")
        )
    )

    assert len(client.calls) == 2
    assert "Previous Output Violation" in client.calls[1][0]
    assert result.frames[0].origin == "extracted"
    assert result.warnings == []


def test_extraction_keeps_a_frame_without_a_verified_span_after_the_retry() -> None:
    description = "Customer books a service."
    client = SequentialStructuredLlmClient(
        [_output(_frame(description, "Client")), _output(_frame(description, "Client"))]
    )

    result = asyncio.run(
        FrameExtractionService(client, max_description_length=100).extract(
            FrameExtractionRequest(description=description, language="en")
        )
    )

    assert len(client.calls) == 2
    assert result.frames[0].spans == []
    assert result.frames[0].origin == "unverified"
    assert result.warnings[0].frame_id == "book-service"


def test_extraction_returns_frames_not_uml_diagram_elements() -> None:
    description = "Customer books a service."
    client = SequentialStructuredLlmClient([_output(_frame(description, "Customer"))])

    result = asyncio.run(
        FrameExtractionService(client, max_description_length=100).extract(
            FrameExtractionRequest(description=description, language="en")
        )
    )

    assert client.calls[0][1] is RequirementFrameExtractionOutput
    assert result.frames[0].action == "books"
    assert "UML" not in result.model_dump_json()


def test_extraction_rejects_invalid_structured_output() -> None:
    client = SequentialStructuredLlmClient([InvalidStructuredOutputError()])

    with pytest.raises(InvalidFrameExtraction, match="requirement frames"):
        asyncio.run(
            FrameExtractionService(client, max_description_length=100).extract(
                FrameExtractionRequest(description="Customer books a service.", language="en")
            )
        )


def test_extraction_enforces_the_configured_description_limit() -> None:
    client = SequentialStructuredLlmClient([])

    with pytest.raises(InvalidFrameExtraction, match="requirement frames"):
        asyncio.run(
            FrameExtractionService(client, max_description_length=3).extract(
                FrameExtractionRequest(description="Customer", language="en")
            )
        )

    assert client.calls == []


def _frame(description: str, span_text: str) -> RequirementFrame:
    return RequirementFrame(
        id="book-service",
        actor="Customer",
        action="books",
        object="service",
        spans=[
            SourceSpan(
                start_offset=0,
                end_offset=8,
                text=span_text,
                origin="extracted",
            )
        ],
        origin="extracted",
    )


def _output(frame: RequirementFrame) -> RequirementFrameExtractionOutput:
    return RequirementFrameExtractionOutput(frames=[frame])
