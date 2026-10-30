from collections.abc import Iterable
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

Origin = Annotated[
    str,
    Field(
        pattern=r"^(extracted|unverified|derived:[a-z][a-z0-9-]*)$",
        description="extracted, unverified, or derived:<requirement-frame-id>.",
    ),
]


class ContractSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class SourceSpan(ContractSchema):
    start_offset: int = Field(
        ge=0,
        serialization_alias="startOffset",
        description="Inclusive character offset in the input.",
    )
    end_offset: int = Field(
        gt=0,
        serialization_alias="endOffset",
        description="Exclusive character offset in the input.",
    )
    text: str = Field(min_length=1, description="Exact substring from the input description.")
    origin: Origin = Field(description="How this source fragment was obtained.")
    similarity_score: float | None = Field(
        default=None,
        ge=0,
        le=1,
        serialization_alias="similarityScore",
        description="Optional similarity score for a non-exact supporting match.",
    )
    embedding_model_version: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        serialization_alias="embeddingModelVersion",
        description="Embedding model version used for the similarity score.",
    )


def validate_source_spans(description: str, spans: Iterable[SourceSpan]) -> None:
    for span in spans:
        if span.start_offset >= span.end_offset or span.end_offset > len(description):
            raise ValueError("Source span offsets are outside the description")
        if description[span.start_offset : span.end_offset] != span.text:
            raise ValueError("Source span text does not match the description")
