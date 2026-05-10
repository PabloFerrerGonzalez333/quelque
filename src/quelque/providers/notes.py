from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from collections import Counter

from openai import OpenAI
from google import genai
from google.genai import types

from ..schemas import LectureNotesSections


class BaseNotesProvider(ABC):
    model_name: str

    @abstractmethod
    def generate(self, transcript: str, language_hint: str | None = None) -> LectureNotesSections:
        raise NotImplementedError


class OpenAINotesProvider(BaseNotesProvider):
    def __init__(self, api_key: str, model_name: str) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

    def generate(self, transcript: str, language_hint: str | None = None) -> LectureNotesSections:
        system_prompt = (
            "You convert lecture transcripts into concise study materials. "
            "Return valid JSON only, following the requested schema exactly."
        )
        user_prompt = (
            f"Language hint: {language_hint or 'auto'}.\n"
            "Turn the transcript below into a clean sanitized transcript (fix speech-to-text errors, add proper punctuation and paragraphs), "
            "a concise summary, key takeaways, study notes, glossary items, and action items.\n\n"
            f"Transcript:\n{transcript}"
        )
        response = self.client.chat.completions.create(
            model=self.model_name,
            temperature=0.2,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "lecture_notes",
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "sanitized_transcript": {"type": "string"},
                            "summary": {"type": "string"},
                            "key_takeaways": {"type": "array", "items": {"type": "string"}},
                            "study_notes": {"type": "array", "items": {"type": "string"}},
                            "glossary": {"type": "array", "items": {"type": "string"}},
                            "action_items": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": [
                            "sanitized_transcript",
                            "summary",
                            "key_takeaways",
                            "study_notes",
                            "glossary",
                            "action_items",
                        ],
                    },
                    "strict": True,
                },
            },
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content or "{}"
        return LectureNotesSections.model_validate(json.loads(content))


class GoogleNotesProvider(BaseNotesProvider):
    def __init__(self, api_key: str, model_name: str) -> None:
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def generate(self, transcript: str, language_hint: str | None = None) -> LectureNotesSections:
        system_prompt = (
            "You convert lecture transcripts into concise study materials. "
            "Return valid JSON only, following the requested schema exactly."
        )
        user_prompt = (
            f"Language hint: {language_hint or 'auto'}.\n"
            "Turn the transcript below into a clean sanitized transcript (fix speech-to-text errors, add proper punctuation and paragraphs), "
            "a concise summary, key takeaways, study notes, glossary items, and action items.\n\n"
            f"Transcript:\n{transcript}"
        )
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Content(
                    role="user", 
                    parts=[types.Part.from_text(text=system_prompt + "\n\n" + user_prompt)]
                )
            ],
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
                response_schema=LectureNotesSections.model_json_schema(),
            )
        )
        content = response.text or "{}"
        return LectureNotesSections.model_validate(json.loads(content))


class HuggingFaceNotesProvider(BaseNotesProvider):
    def __init__(self, api_key: str | None, model_name: str) -> None:
        from huggingface_hub import InferenceClient
        self.client = InferenceClient(api_key=api_key)
        self.model_name = model_name

    def generate(self, transcript: str, language_hint: str | None = None) -> LectureNotesSections:
        schema = LectureNotesSections.model_json_schema()
        system_prompt = (
            "You convert lecture transcripts into concise study materials. "
            "Return valid JSON ONLY, strictly matching this schema:\n"
            f"{json.dumps(schema)}\n"
            "Do not output markdown code blocks or any other text around the JSON."
        )
        user_prompt = (
            f"Language hint: {language_hint or 'auto'}.\n"
            "Turn the transcript below into a clean sanitized transcript (fix speech-to-text errors, add proper punctuation and paragraphs), "
            "a concise summary, key takeaways, study notes, glossary items, and action items.\n\n"
            f"Transcript:\n{transcript}"
        )
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content or "{}"
        try:
            return LectureNotesSections.model_validate(json.loads(content))
        except Exception:
            clean = content.replace("```json", "").replace("```", "").strip()
            return LectureNotesSections.model_validate(json.loads(clean))


class LocalHeuristicNotesProvider(BaseNotesProvider):
    def __init__(self) -> None:
        self.model_name = "heuristic-local"

    def generate(self, transcript: str, language_hint: str | None = None) -> LectureNotesSections:
        sentences = _split_sentences(transcript)
        if not sentences:
            return LectureNotesSections(
                sanitized_transcript=transcript,
                summary="",
                key_takeaways=[],
                study_notes=[],
                glossary=[],
                action_items=[],
            )

        ranked = _rank_sentences(sentences)
        summary = " ".join(sentences[:2]) if len(sentences) <= 2 else " ".join(ranked[:2])
        key_takeaways = ranked[:4]
        study_notes = [f"Review: {sentence}" for sentence in ranked[:5]]
        glossary = _extract_glossary(transcript)
        action_items = _extract_action_items(sentences)
        return LectureNotesSections(
            sanitized_transcript=transcript,
            summary=summary,
            key_takeaways=key_takeaways,
            study_notes=study_notes,
            glossary=glossary,
            action_items=action_items,
        )


def _split_sentences(transcript: str) -> list[str]:
    raw = re.split(r"(?<=[.!?])\s+|\n+", transcript)
    return [sentence.strip() for sentence in raw if sentence.strip()]


def _rank_sentences(sentences: list[str]) -> list[str]:
    counts = Counter(
        word.lower()
        for sentence in sentences
        for word in re.findall(r"\b\w+\b", sentence)
    )
    ranked = sorted(
        sentences,
        key=lambda sentence: sum(counts[word.lower()] for word in re.findall(r"\b\w+\b", sentence)),
        reverse=True,
    )
    seen: set[str] = set()
    unique_ranked: list[str] = []
    for sentence in ranked:
        if sentence not in seen:
            unique_ranked.append(sentence)
            seen.add(sentence)
    return unique_ranked


def _extract_glossary(transcript: str) -> list[str]:
    words = re.findall(r"\b[A-Za-z][A-Za-z\-]{5,}\b", transcript)
    counts = Counter(word.lower() for word in words)
    entries: list[str] = []
    for word, _count in counts.most_common(5):
        entries.append(f"{word}: recurring concept mentioned in the transcript")
    return entries


def _extract_action_items(sentences: list[str]) -> list[str]:
    keywords = (
        "remember",
        "review",
        "submit",
        "read",
        "prepare",
        "study",
        "complete",
        "practice",
    )
    actions = [
        sentence
        for sentence in sentences
        if any(keyword in sentence.lower() for keyword in keywords)
    ]
    return actions[:5]
