from pathlib import Path

from quelque.config import AppConfig
from quelque.pipeline import QuelquePipeline
from quelque.schemas import LectureNotesSections, TranscriptResult


class SmokeTranscriber:
    model_name = "smoke"

    def transcribe(self, audio_path: Path, language_hint: str | None = None) -> TranscriptResult:
        return TranscriptResult(
            text="Synthetic sample transcript for smoke testing.",
            duration_seconds=1.0,
            detected_language="en",
        )


class SmokeNotes:
    model_name = "smoke-notes"

    def generate(self, transcript: str, language_hint: str | None = None) -> LectureNotesSections:
        return LectureNotesSections(
            summary="Synthetic summary.",
            key_takeaways=["Synthetic takeaway."],
            study_notes=["Synthetic note."],
            glossary=["synthetic: generated for testing"],
            action_items=[],
        )


class SmokePipeline(QuelquePipeline):
    def _build_transcriber(self, provider: str):  # noqa: ANN001
        return SmokeTranscriber()

    def _build_note_builder(self, provider: str):  # noqa: ANN001
        return SmokeNotes()


def test_smoke_sample_fixture_runs(tmp_path: Path):
    sample_path = Path("samples/tiny_sanitized_sample.wav")
    pipeline = SmokePipeline(
        AppConfig(
            cache_dir=tmp_path / "cache",
            export_dir=tmp_path / "exports",
        )
    )
    result = pipeline.run(sample_path, transcription_provider="local", notes_provider="local")
    assert result.notes.summary == "Synthetic summary."
