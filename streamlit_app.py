from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from quelque.config import AppConfig
from quelque.exporters import render_docx, render_markdown, render_pdf
from quelque.pipeline import QuelquePipeline
from quelque.schemas import PipelineResult

st.set_page_config(page_title="Quelque", page_icon="Q", layout="wide")


def main() -> None:
    config = AppConfig()
    pipeline = QuelquePipeline(config)
    _render_styles()

    col_main, col_upload = st.columns([1.5, 1], gap="large")

    with col_main:
        _render_header()
        with st.expander("💡 How it Works", expanded=False):
            st.markdown(
                "When you upload an audio file and press Generate, Quelque runs **two distinct steps** automatically:\n\n"
                "1. **Step 1: Transcription 🎙️** - The audio is processed by an AI model to generate a highly accurate, word-for-word transcript.\n"
                "2. **Step 2: AI Summarization 🧠** - That full transcript is sent to a Language Model (LLM) which analyzes the text and synthesizes it into a concise summary, key takeaways, structured study notes, a glossary, and action items.\n\n"
                "All processing is cached, so uploading the exact same audio file twice will instantly return the previous results without re-running the models."
            )

    with st.sidebar:
        provider_mode = st.radio(
            "Provider mode",
            options=["HuggingFace", "OpenAI", "Gemini"],
            help="Choose the AI engine to generate the notes.",
        )
        language_hint = st.selectbox(
            "Language hint",
            options=["Auto", "English", "Spanish", "French", "German", "Italian"],
            help="This language is enforced across BOTH steps: it forces the transcriber to listen in this language, and instructs the AI to write the final notes in this language.",
        )
        if provider_mode == "HuggingFace":
            key_label = "Hugging Face Token"
        elif provider_mode == "Gemini":
            key_label = "Google AI Studio API Key"
        else:
            key_label = "OpenAI API Key"

        user_api_key = st.text_input(
            key_label,
            type="password",
            help="Provide your own token depending on the chosen mode. It is used ephemerally and not stored.",
        )
        if user_api_key:
            if provider_mode == "OpenAI":
                config.openai_api_key = user_api_key
            elif provider_mode == "Gemini":
                config.google_api_key = user_api_key
            elif provider_mode == "HuggingFace":
                config.hf_api_key = user_api_key
                
        st.markdown("---")
        if provider_mode == "OpenAI":
            st.caption(f"🎙️ Transcription: `{config.openai_transcription_model}`  \n🧠 Summarization: `{config.openai_notes_model}`")
        elif provider_mode == "Gemini":
            st.caption(f"🎙️ Transcription: `faster-whisper {config.local_transcription_model}`  \n🧠 Summarization: `{config.google_notes_model}`")
        elif provider_mode == "HuggingFace":
            st.caption(f"🎙️ Transcription: `faster-whisper {config.local_transcription_model}`  \n🧠 Summarization: `{config.hf_notes_model}`")

        st.caption(f"📦 Max file size: {config.max_upload_mb} MB")

    with col_upload:
        st.markdown("<br>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload lecture audio",
            type=["mp3", "wav", "m4a"],
            help="Drop a lecture, class recording, or study session to generate notes.",
        )

        generate_pressed = st.button(
            "Generate Notes",
            type="primary",
            use_container_width=True,
            disabled=uploaded_file is None,
        )

    st.markdown("---")

    if generate_pressed:
        if uploaded_file is None:
            st.warning("Upload an audio file to continue.")
        else:
            result = _run_pipeline(pipeline, uploaded_file, provider_mode, language_hint)
            if result is not None:
                st.session_state["pipeline_result"] = result

    if "pipeline_result" in st.session_state:
        _render_results(st.session_state["pipeline_result"])


def _run_pipeline(
    pipeline: QuelquePipeline, uploaded_file, provider_mode: str, language_hint: str
) -> PipelineResult | None:
    transcription_provider = "openai" if provider_mode == "OpenAI" else "local"
    if provider_mode == "OpenAI":
        notes_provider = "openai"
    elif provider_mode == "Gemini":
        notes_provider = "google"
    else:
        notes_provider = "huggingface"
    language_map = {
        "Auto": None,
        "English": "en",
        "Spanish": "es",
        "French": "fr",
        "German": "de",
        "Italian": "it"
    }
    hint = language_map.get(language_hint)

    suffix = Path(uploaded_file.name).suffix or ".wav"
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
        prefix="quelque_upload_",
    ) as handle:
        handle.write(uploaded_file.getbuffer())
        temp_path = Path(handle.name)

    try:
        with st.status("Processing audio", expanded=True) as status:
            st.write("Normalizing audio and preparing chunks.")
            st.write(
                f"Using `{transcription_provider}` transcription and `{notes_provider}` notes."
            )
            result = pipeline.run(
                temp_path,
                transcription_provider=transcription_provider,
                notes_provider=notes_provider,
                language_hint=hint,
            )
            st.write(f"Elapsed: {result.elapsed_seconds:.2f}s")
            st.write(f"Detected Language: {result.notes.transcript.detected_language or 'Unknown'}")
            if result.cache_hit:
                st.write("Loaded from cache.")
            status.update(label="Processing complete", state="complete")
            return result
    except Exception as exc:  # noqa: BLE001
        st.error(str(exc))
        return None
    finally:
        temp_path.unlink(missing_ok=True)


def _render_results(result: PipelineResult) -> None:
    notes = result.notes

    tab_sanitized, tab_transcript, tab_notes, tab_exports = st.tabs(["Sanitized Transcript", "Raw Transcript", "Notes", "Exports"])

    with tab_sanitized:
        st.text_area("Sanitized Transcript", notes.sanitized_transcript, height=320)

    with tab_transcript:
        st.text_area("Raw Transcript", notes.transcript.text, height=320)
        if notes.transcript.segments:
            with st.expander("Segments"):
                for segment in notes.transcript.segments[:50]:
                    st.write(f"{segment.start:>7.2f}s - {segment.end:>7.2f}s | {segment.text}")

    with tab_notes:
        st.subheader("Summary")
        st.write(notes.summary)
        st.subheader("Key Takeaways")
        for item in notes.key_takeaways:
            st.write(f"- {item}")
        st.subheader("Study Notes")
        for item in notes.study_notes:
            st.write(f"- {item}")
        st.subheader("Glossary")
        for item in notes.glossary:
            st.write(f"- {item}")
        st.subheader("Action Items")
        if notes.action_items:
            for item in notes.action_items:
                st.write(f"- {item}")
        else:
            st.write("No explicit action items detected.")

    with tab_exports:
        markdown_bytes = render_markdown(notes).encode("utf-8")
        docx_bytes = render_docx(notes)
        pdf_bytes = render_pdf(notes)
        st.download_button(
            "Download Markdown",
            data=markdown_bytes,
            file_name="quelque-notes.md",
            mime="text/markdown",
            use_container_width=True,
        )
        st.download_button(
            "Download DOCX",
            data=docx_bytes,
            file_name="quelque-notes.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
        st.download_button(
            "Download PDF",
            data=pdf_bytes,
            file_name="quelque-notes.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


def _render_header() -> None:
    st.markdown(
        """
        <div class="hero">
          <h1>Quelque</h1>
          <p class="lede">
            Upload an educational audio file to automatically transcribe the speech and synthesize AI-driven study notes.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255, 209, 102, 0.22), transparent 35%),
                radial-gradient(circle at top right, rgba(17, 138, 178, 0.18), transparent 28%),
                linear-gradient(180deg, #f5efe6 0%, #fbfaf7 48%, #eef4f7 100%);
        }
        .hero {
            padding: 0.5rem 0 1rem 0;
        }
        .hero h1 {
            font-size: 4rem;
            line-height: 1;
            margin: 0;
            color: #0f766e;
        }
        .eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.18em;
            font-size: 0.8rem;
            color: #0f766e;
            font-weight: 700;
        }
        .lede {
            max-width: 48rem;
            color: #334155;
            font-size: 1.05rem;
        }
        div[data-testid="stStatusWidget"] {
            background: rgba(255, 255, 255, 0.7);
            border: 1px solid rgba(15, 23, 42, 0.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
