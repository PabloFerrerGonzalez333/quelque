from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from openai import OpenAI

from ..schemas import TranscriptResult, TranscriptSegment


def _coerce_segments(
    raw_segments: list[Any] | None, offset_seconds: float = 0.0
) -> list[TranscriptSegment]:
    segments: list[TranscriptSegment] = []
    for raw in raw_segments or []:
        start = float(getattr(raw, "start", 0.0)) + offset_seconds
        end = float(getattr(raw, "end", start)) + offset_seconds
        text = str(getattr(raw, "text", "")).strip()
        if text:
            segments.append(TranscriptSegment(start=start, end=end, text=text))
    return segments


class BaseTranscriptionProvider(ABC):
    model_name: str

    @abstractmethod
    def transcribe(self, audio_path: Path, language_hint: str | None = None) -> TranscriptResult:
        raise NotImplementedError


class OpenAITranscriptionProvider(BaseTranscriptionProvider):
    def __init__(self, api_key: str, model_name: str) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

    def transcribe(self, audio_path: Path, language_hint: str | None = None) -> TranscriptResult:
        with audio_path.open("rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model=self.model_name,
                file=audio_file,
                language=language_hint or None,
                response_format="verbose_json",
            )
        return TranscriptResult(
            text=str(getattr(response, "text", "")).strip(),
            segments=_coerce_segments(getattr(response, "segments", None)),
            duration_seconds=float(getattr(response, "duration", 0.0) or 0.0),
            detected_language=getattr(response, "language", language_hint),
        )


class LocalTranscriptionProvider(BaseTranscriptionProvider):
    def __init__(self, model_name: str, device: str = "auto", compute_type: str = "auto") -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "Local transcription requires faster-whisper to be installed."
            ) from exc

        self.model_name = model_name
        self._model = WhisperModel(model_name, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: Path, language_hint: str | None = None) -> TranscriptResult:
        segments, info = self._model.transcribe(
            str(audio_path),
            language=language_hint or None,
            vad_filter=True,
            beam_size=1,
        )
        collected_segments: list[TranscriptSegment] = []
        texts: list[str] = []
        for segment in segments:
            text = segment.text.strip()
            if not text:
                continue
            texts.append(text)
            collected_segments.append(
                TranscriptSegment(start=float(segment.start), end=float(segment.end), text=text)
            )
        return TranscriptResult(
            text=" ".join(texts).strip(),
            segments=collected_segments,
            duration_seconds=float(getattr(info, "duration", 0.0) or 0.0),
            detected_language=getattr(info, "language", language_hint),
        )
