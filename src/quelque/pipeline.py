from __future__ import annotations

import tempfile
import time
from pathlib import Path

from .audio import normalize_audio
from .cache import compute_cache_key, load_cached_result, save_cached_result
from .chunking import build_chunk_ranges, materialize_chunks
from .config import AppConfig
from .providers.notes import BaseNotesProvider, LocalHeuristicNotesProvider, OpenAINotesProvider, GoogleNotesProvider, HuggingFaceNotesProvider
from .providers.transcription import (
    BaseTranscriptionProvider,
    LocalTranscriptionProvider,
    OpenAITranscriptionProvider,
)
from .schemas import LectureNotesResult, PipelineResult, TranscriptResult, TranscriptSegment


class QuelquePipeline:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.config.ensure_directories()

    def run(
        self,
        audio_path: Path,
        *,
        transcription_provider: str | None = None,
        notes_provider: str | None = None,
        language_hint: str | None = None,
    ) -> PipelineResult:
        start = time.perf_counter()
        chosen_transcription_provider = (
            transcription_provider or self.config.default_transcription_provider
        )
        chosen_notes_provider = notes_provider or self.config.default_notes_provider
        transcription_model = (
            self.config.openai_transcription_model
            if chosen_transcription_provider == "openai"
            else self.config.local_transcription_model
        )
        notes_model = (
            self.config.openai_notes_model
            if chosen_notes_provider == "openai"
            else "heuristic-local"
        )
        cache_key = compute_cache_key(
            audio_path,
            provider=chosen_transcription_provider,
            notes_provider=chosen_notes_provider,
            transcription_model=transcription_model,
            notes_model=notes_model,
            language_hint=language_hint,
            chunk_duration_seconds=self.config.chunk_duration_seconds,
            chunk_overlap_seconds=self.config.chunk_overlap_seconds,
        )
        cached = load_cached_result(self.config.cache_dir, cache_key)
        if cached is not None:
            return PipelineResult(
                notes=cached,
                cache_hit=True,
                cache_key=cache_key,
                elapsed_seconds=time.perf_counter() - start,
            )

        transcriber = self._build_transcriber(chosen_transcription_provider)
        note_builder = self._build_note_builder(chosen_notes_provider)
        notes = self._process(audio_path, transcriber, note_builder, language_hint)
        save_cached_result(self.config.cache_dir, cache_key, notes)
        return PipelineResult(
            notes=notes,
            cache_hit=False,
            cache_key=cache_key,
            elapsed_seconds=time.perf_counter() - start,
        )

    def _build_transcriber(self, provider: str) -> BaseTranscriptionProvider:
        if provider == "openai":
            if not self.config.openai_api_key:
                raise RuntimeError("OPENAI_API_KEY is required for hosted transcription mode.")
            return OpenAITranscriptionProvider(
                api_key=self.config.openai_api_key,
                model_name=self.config.openai_transcription_model,
            )
        if provider == "local":
            return LocalTranscriptionProvider(
                model_name=self.config.local_transcription_model,
                device=self.config.local_device,
                compute_type=self.config.local_compute_type,
            )
        raise ValueError(f"Unsupported transcription provider: {provider}")

    def _build_note_builder(self, provider: str) -> BaseNotesProvider:
        if provider == "openai":
            if not self.config.openai_api_key:
                raise RuntimeError("OPENAI_API_KEY is required for hosted notes mode.")
            return OpenAINotesProvider(
                api_key=self.config.openai_api_key,
                model_name=self.config.openai_notes_model,
            )
        if provider == "google":
            if not self.config.google_api_key:
                raise RuntimeError("GOOGLE_API_KEY is required for google notes mode.")
            return GoogleNotesProvider(
                api_key=self.config.google_api_key,
                model_name=self.config.google_notes_model,
            )
        if provider == "huggingface":
            if not self.config.hf_api_key:
                raise RuntimeError(
                    "HF_TOKEN is missing! Even though the Hugging Face API is free, it requires an authentication token to prevent spam. "
                    "Please paste your Hugging Face access token into the 'API Key' box in the sidebar."
                )
            return HuggingFaceNotesProvider(
                api_key=self.config.hf_api_key,
                model_name=self.config.hf_notes_model,
            )
        if provider == "local":
            return LocalHeuristicNotesProvider()
        raise ValueError(f"Unsupported notes provider: {provider}")

    def _process(
        self,
        audio_path: Path,
        transcriber: BaseTranscriptionProvider,
        note_builder: BaseNotesProvider,
        language_hint: str | None,
    ) -> LectureNotesResult:
        with tempfile.TemporaryDirectory(prefix="quelque_") as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            normalized = normalize_audio(audio_path, temp_dir / "normalized")
            ranges = build_chunk_ranges(
                normalized.duration_seconds,
                self.config.chunk_duration_seconds,
                self.config.chunk_overlap_seconds,
            )
            chunks = materialize_chunks(normalized.path, ranges, temp_dir / "chunks")

            merged_texts: list[str] = []
            merged_segments: list[TranscriptSegment] = []
            detected_language = language_hint
            for chunk in chunks:
                partial = transcriber.transcribe(chunk.path, language_hint=language_hint)
                if partial.text:
                    merged_texts.append(partial.text)
                for segment in partial.segments:
                    merged_segments.append(
                        TranscriptSegment(
                            start=segment.start + chunk.start_seconds,
                            end=segment.end + chunk.start_seconds,
                            text=segment.text,
                        )
                    )
                detected_language = partial.detected_language or detected_language

            transcript = TranscriptResult(
                text="\n\n".join(text.strip() for text in merged_texts if text.strip()),
                segments=merged_segments,
                duration_seconds=normalized.duration_seconds,
                detected_language=detected_language,
            )
            sections = note_builder.generate(transcript.text, language_hint=language_hint)
            return LectureNotesResult(
                transcript=transcript,
                sanitized_transcript=sections.sanitized_transcript,
                summary=sections.summary,
                key_takeaways=sections.key_takeaways,
                study_notes=sections.study_notes,
                glossary=sections.glossary,
                action_items=sections.action_items,
                exports={
                    "markdown": "quelque-notes.md",
                    "docx": "quelque-notes.docx",
                    "pdf": "quelque-notes.pdf",
                },
            )
