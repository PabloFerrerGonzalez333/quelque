from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import AppConfig
from .exporters import render_markdown
from .pipeline import QuelquePipeline


def main() -> None:
    parser = argparse.ArgumentParser(prog="quelque", description="Lecture-to-notes assistant")
    subparsers = parser.add_subparsers(dest="command", required=True)

    transcribe_parser = subparsers.add_parser("transcribe", help="Transcribe an audio file")
    transcribe_parser.add_argument("file", type=Path)
    transcribe_parser.add_argument("--provider", choices=["openai", "local"], default=None)
    transcribe_parser.add_argument("--language", default=None)

    notes_parser = subparsers.add_parser("notes", help="Generate lecture notes from an audio file")
    notes_parser.add_argument("file", type=Path)
    notes_parser.add_argument("--transcription-provider", choices=["openai", "local"], default=None)
    notes_parser.add_argument("--notes-provider", choices=["openai", "local"], default=None)
    notes_parser.add_argument("--language", default=None)
    notes_parser.add_argument("--format", choices=["json", "markdown"], default="markdown")

    args = parser.parse_args()
    pipeline = QuelquePipeline(AppConfig())

    if args.command == "transcribe":
        result = pipeline.run(
            args.file,
            transcription_provider=args.provider,
            notes_provider="local",
            language_hint=args.language,
        )
        print(result.notes.transcript.text)
        return

    if args.command == "notes":
        result = pipeline.run(
            args.file,
            transcription_provider=args.transcription_provider,
            notes_provider=args.notes_provider,
            language_hint=args.language,
        )
        if args.format == "json":
            print(json.dumps(result.notes.model_dump(mode="json"), indent=2))
        else:
            print(render_markdown(result.notes))
