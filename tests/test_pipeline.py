from pathlib import Path

from quelque.config import AppConfig
from quelque.pipeline import QuelquePipeline
from quelque.schemas import LectureNotesSections, TranscriptResult


class DummyTranscriber:
    model_name = "dummy"

    def transcribe(self, audio_path: Path, language_hint: str | None = None) -> TranscriptResult:
        return TranscriptResult(
            text="This lecture covers caching. Review chapter two.",
            duration_seconds=1.0,
            detected_language=language_hint or "en",
        )


class DummyNotesProvider:
    model_name = "dummy"

    def generate(self, transcript: str, language_hint: str | None = None) -> LectureNotesSections:
        return LectureNotesSections(
            summary="Caching helps repeat runs.",
            key_takeaways=["Caching reduces repeated work."],
            study_notes=["Review the caching pipeline."],
            glossary=["cache: stored result used later"],
            action_items=["Review chapter two."],
        )


class RoutingPipeline(QuelquePipeline):
    def _build_transcriber(self, provider: str):  # noqa: ANN001
        self.last_transcription_provider = provider
        return DummyTranscriber()

    def _build_note_builder(self, provider: str):  # noqa: ANN001
        self.last_notes_provider = provider
        return DummyNotesProvider()


def test_pipeline_routes_providers_and_caches(tmp_path: Path):
    audio_path = Path("samples/tiny_sanitized_sample.wav")
    pipeline = RoutingPipeline(
        AppConfig(
            cache_dir=tmp_path / "cache",
            export_dir=tmp_path / "exports",
        )
    )

    first = pipeline.run(audio_path, transcription_provider="local", notes_provider="local")
    second = pipeline.run(audio_path, transcription_provider="local", notes_provider="local")

    assert first.cache_hit is False
    assert second.cache_hit is True
    assert pipeline.last_transcription_provider == "local"
    assert pipeline.last_notes_provider == "local"
    assert second.notes.summary == "Caching helps repeat runs."
