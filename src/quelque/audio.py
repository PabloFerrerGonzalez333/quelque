from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel
from pydub import AudioSegment


class NormalizedAudio(BaseModel):
    path: Path
    duration_seconds: float


def normalize_audio(input_path: Path, output_dir: Path) -> NormalizedAudio:
    output_dir.mkdir(parents=True, exist_ok=True)
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    output_path = output_dir / f"{input_path.stem}_normalized.wav"
    audio.export(output_path, format="wav")
    return NormalizedAudio(path=output_path, duration_seconds=len(audio) / 1000)
