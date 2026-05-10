from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .schemas import LectureNotesResult


def compute_cache_key(
    audio_path: Path,
    *,
    provider: str,
    notes_provider: str,
    transcription_model: str,
    notes_model: str,
    language_hint: str | None,
    chunk_duration_seconds: int,
    chunk_overlap_seconds: int,
) -> str:
    digest = hashlib.sha256()
    digest.update(audio_path.read_bytes())
    digest.update(
        json.dumps(
            {
                "provider": provider,
                "notes_provider": notes_provider,
                "transcription_model": transcription_model,
                "notes_model": notes_model,
                "language_hint": language_hint or "",
                "chunk_duration_seconds": chunk_duration_seconds,
                "chunk_overlap_seconds": chunk_overlap_seconds,
            },
            sort_keys=True,
        ).encode("utf-8")
    )
    return digest.hexdigest()


def cache_path(cache_dir: Path, cache_key: str) -> Path:
    return cache_dir / f"{cache_key}.json"


def load_cached_result(cache_dir: Path, cache_key: str) -> LectureNotesResult | None:
    path = cache_path(cache_dir, cache_key)
    if not path.exists():
        return None
    return LectureNotesResult.model_validate_json(path.read_text(encoding="utf-8"))


def save_cached_result(cache_dir: Path, cache_key: str, result: LectureNotesResult) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_path(cache_dir, cache_key)
    path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return path
