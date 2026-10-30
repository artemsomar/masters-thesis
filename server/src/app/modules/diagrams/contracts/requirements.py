from typing import Annotated

from pydantic import Field, model_validator

from app.modules.diagrams.contracts.provenance import ContractSchema, Origin, SourceSpan

FrameIdentifier = Annotated[
    str,
    Field(min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9-]*$"),
]
RequirementText = Annotated[str, Field(min_length=1, max_length=500)]
LanguageCode = Annotated[str, Field(pattern=r"^[a-z]{2,3}(?:-[A-Z]{2})?$")]


class RequirementFrame(ContractSchema):
    id: FrameIdentifier = Field(description="Stable identifier of this atomic requirement frame.")
    actor: RequirementText | None = Field(
        default=None, description="Role that performs the action."
    )
    action: RequirementText | None = Field(
        default=None, description="Atomic action from the source."
    )
    object: RequirementText | None = Field(default=None, description="Target of the action.")
    condition: RequirementText | None = Field(
        default=None, description="Optional condition stated in the source."
    )
    spans: list[SourceSpan] = Field(
        default_factory=list, description="Exact source fragments supporting this frame."
    )
    origin: Origin = Field(description="How this frame is supported by the input description.")


class FrameExtractionRequest(ContractSchema):
    description: str = Field(min_length=1, description="Full system description to analyse once.")
    language: LanguageCode = Field(description="BCP-47-like language code of the description.")


class RequirementFrameExtractionOutput(ContractSchema):
    frames: list[RequirementFrame] = Field(
        description="Atomic requirement frames; never UML elements or use cases."
    )

    @model_validator(mode="after")
    def frame_identifiers_are_unique(self) -> "RequirementFrameExtractionOutput":
        if len({frame.id for frame in self.frames}) != len(self.frames):
            raise ValueError("Requirement frame identifiers must be unique")
        return self


class FrameExtractionWarning(ContractSchema):
    frame_id: FrameIdentifier = Field(description="Identifier of the affected frame.")
    reason: str = Field(min_length=1, max_length=500, description="Why the frame is unverified.")


class FrameExtractionResult(ContractSchema):
    frames: list[RequirementFrame] = Field(description="Frames passed to the next pipeline step.")
    warnings: list[FrameExtractionWarning] = Field(
        default_factory=list, description="Visible diagnostics for frames without verified sources."
    )
    prompt_version: str = Field(
        min_length=1, max_length=100, description="Version of the extraction prompt used."
    )
