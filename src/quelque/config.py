from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


@dataclass(slots=True)
class AppConfig:
    default_transcription_provider: str = field(
        default_factory=lambda: os.getenv("QUELQUE_TRANSCRIPTION_PROVIDER", "local")
    )
    default_notes_provider: str = field(
        default_factory=lambda: os.getenv("QUELQUE_NOTES_PROVIDER", "huggingface")
    )
    openai_transcription_model: str = field(
        default_factory=lambda: os.getenv(
            "QUELQUE_OPENAI_TRANSCRIPTION_MODEL", "gpt-4o-mini-transcribe"
        )
    )
    openai_notes_model: str = field(
        default_factory=lambda: os.getenv("QUELQUE_OPENAI_NOTES_MODEL", "gpt-5.4-mini")
    )
    google_notes_model: str = field(
        default_factory=lambda: os.getenv("QUELQUE_GOOGLE_NOTES_MODEL", "gemini-2.5-flash")
    )
    hf_notes_model: str = field(
        default_factory=lambda: os.getenv("QUELQUE_HF_NOTES_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    )
    local_transcription_model: str = field(
        default_factory=lambda: os.getenv("QUELQUE_LOCAL_TRANSCRIPTION_MODEL", "small")
    )
    local_device: str = field(default_factory=lambda: os.getenv("QUELQUE_LOCAL_DEVICE", "auto"))
    local_compute_type: str = field(
        default_factory=lambda: os.getenv("QUELQUE_LOCAL_COMPUTE_TYPE", "auto")
    )
    chunk_duration_seconds: int = field(
        default_factory=lambda: _env_int("QUELQUE_CHUNK_DURATION_SECONDS", 900)
    )
    chunk_overlap_seconds: int = field(
        default_factory=lambda: _env_int("QUELQUE_CHUNK_OVERLAP_SECONDS", 30)
    )
    max_upload_mb: int = field(default_factory=lambda: _env_int("QUELQUE_MAX_UPLOAD_MB", 200))
    cache_dir: Path = field(default_factory=lambda: Path(os.getenv("QUELQUE_CACHE_DIR", ".cache")))
    export_dir: Path = field(
        default_factory=lambda: Path(os.getenv("QUELQUE_EXPORT_DIR", "exports"))
    )
    sample_path: Path = field(
        default_factory=lambda: Path(
            os.getenv("QUELQUE_SAMPLE_PATH", "samples/tiny_sanitized_sample.wav")
        )
    )
    openai_api_key: str | None = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"), repr=False)
    google_api_key: str | None = field(default_factory=lambda: os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"), repr=False)
    hf_api_key: str | None = field(default_factory=lambda: os.getenv("HF_TOKEN"), repr=False)

    def ensure_directories(self) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)

