from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel
from pydub import AudioSegment


class AudioChunk(BaseModel):
    path: Path
    start_seconds: float
    end_seconds: float


def build_chunk_ranges(
    duration_seconds: float, chunk_duration_seconds: int, overlap_seconds: int
) -> list[tuple[float, float]]:
    if duration_seconds <= 0:
        return []

    if chunk_duration_seconds <= 0:
        raise ValueError("chunk_duration_seconds must be positive")

    step = chunk_duration_seconds - overlap_seconds
    if step <= 0:
        raise ValueError("overlap_seconds must be smaller than chunk_duration_seconds")

    windows: list[tuple[float, float]] = []
    start = 0.0
    while start < duration_seconds:
        end = min(start + chunk_duration_seconds, duration_seconds)
        windows.append((start, end))
        if end >= duration_seconds:
            break
        start += step
    return windows


def materialize_chunks(
    normalized_audio_path: Path, ranges: list[tuple[float, float]], output_dir: Path
) -> list[AudioChunk]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source = AudioSegment.from_file(normalized_audio_path)

    chunks: list[AudioChunk] = []
    for index, (start_seconds, end_seconds) in enumerate(ranges, start=1):
        start_ms = int(start_seconds * 1000)
        end_ms = int(end_seconds * 1000)
        chunk_audio = source[start_ms:end_ms]
        chunk_path = output_dir / f"{normalized_audio_path.stem}_chunk_{index:03d}.wav"
        chunk_audio.export(chunk_path, format="wav")
        chunks.append(
            AudioChunk(path=chunk_path, start_seconds=start_seconds, end_seconds=end_seconds)
        )
    return chunks
