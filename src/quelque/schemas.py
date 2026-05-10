from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

ProviderName = Literal["openai", "local"]


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class TranscriptionRequest(BaseModel):
    audio_path: Path
    language_hint: str | None = None
    provider: ProviderName = "openai"


class TranscriptResult(BaseModel):
    text: str
    segments: list[TranscriptSegment] = Field(default_factory=list)
    duration_seconds: float
    detected_language: str | None = None


class LectureNotesSections(BaseModel):
    sanitized_transcript: str
    summary: str
    key_takeaways: list[str] = Field(default_factory=list)
    study_notes: list[str] = Field(default_factory=list)
    glossary: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)


class LectureNotesResult(BaseModel):
    transcript: TranscriptResult
    sanitized_transcript: str
    summary: str
    key_takeaways: list[str] = Field(default_factory=list)
    study_notes: list[str] = Field(default_factory=list)
    glossary: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    exports: dict[str, str] = Field(default_factory=dict)


class PipelineResult(BaseModel):
    notes: LectureNotesResult
    cache_hit: bool = False
    cache_key: str
    elapsed_seconds: float
