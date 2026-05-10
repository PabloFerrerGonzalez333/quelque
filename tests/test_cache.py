from pathlib import Path

from quelque.cache import compute_cache_key, load_cached_result, save_cached_result
from quelque.schemas import LectureNotesResult, TranscriptResult


def test_cache_roundtrip(tmp_path: Path):
    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(b"audio")
    cache_dir = tmp_path / "cache"
    key = compute_cache_key(
        audio_path,
        provider="local",
        notes_provider="local",
        transcription_model="small",
        notes_model="heuristic-local",
        language_hint=None,
        chunk_duration_seconds=300,
        chunk_overlap_seconds=30,
    )
    result = LectureNotesResult(
        transcript=TranscriptResult(text="hello", duration_seconds=1.0, detected_language="en"),
        summary="summary",
        key_takeaways=["a"],
        study_notes=["b"],
        glossary=["c"],
        action_items=["d"],
    )
    save_cached_result(cache_dir, key, result)
    loaded = load_cached_result(cache_dir, key)
    assert loaded is not None
    assert loaded.summary == "summary"
