from quelque.exporters import render_docx, render_markdown, render_pdf
from quelque.schemas import LectureNotesResult, TranscriptResult


def _result() -> LectureNotesResult:
    return LectureNotesResult(
        transcript=TranscriptResult(
            text="Transcript",
            duration_seconds=1.0,
            detected_language="en",
        ),
        summary="Summary",
        key_takeaways=["One"],
        study_notes=["Two"],
        glossary=["Three"],
        action_items=["Four"],
    )


def test_markdown_export_contains_sections():
    markdown = render_markdown(_result())
    assert "## Summary" in markdown
    assert "## Transcript" in markdown


def test_binary_exports_return_bytes():
    assert render_docx(_result())
    assert render_pdf(_result())
