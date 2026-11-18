from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceManifest(StrictModel):
    source_id: str
    source_uri: str
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    original_filename: str
    size_bytes: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    importer_version: str


class BenchmarkRecord(BaseModel):
    """Tolerant input model: unknown upstream fields are retained in source metadata."""

    model_config = ConfigDict(extra="allow")
    index: str | int | None = None
    origin_query: str | None = None
    prompt: str | None = None
    prediction: Any | None = None
    raw_output: Any | None = None
    ground_truth: Any | None = None
    score: float | None = None
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    cost: float | None = Field(default=None, ge=0)

    @field_validator("origin_query", "prompt")
    @classmethod
    def nonempty_text(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("text must not be blank")
        return value


class OpenRouterModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    name: str | None = None
    canonical_slug: str | None = None
    context_length: int | None = None
    architecture: dict[str, Any] | None = None
    pricing: dict[str, Any] = Field(default_factory=dict)
    supported_parameters: list[str] = Field(default_factory=list)
