# Usage

## Local setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev,docs]
copy .env.example .env
streamlit run streamlit_app.py
```

Set `OPENAI_API_KEY` in `.env` if you want hosted mode.

## CLI examples

```bash
quelque transcribe samples/tiny_sanitized_sample.wav --provider local
quelque notes samples/tiny_sanitized_sample.wav --transcription-provider local --notes-provider local
```

## Build the docs site

```bash
sphinx-build -b html docs/source docs/build/html
```

The GitHub Pages workflow publishes the same docs structure automatically from `main`.
