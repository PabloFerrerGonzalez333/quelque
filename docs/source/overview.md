# Overview

Quelque turns lecture audio into:

- a transcript
- a concise summary
- key takeaways
- study notes
- glossary items
- action items

The repository is intentionally productized for public presentation:

- clean package layout in `src/quelque/`
- Streamlit app for interactive demos
- CLI for reproducible workflows
- Sphinx docs for GitHub Pages
- notebooks preserved as portfolio artifacts

## Runtime Modes

### Hosted mode

- transcription with `gpt-4o-mini-transcribe`
- note generation with `gpt-5.4-mini`
- best fit for fast public demos

### Local fallback

- transcription with `faster-whisper`
- heuristic note extraction
- useful when API credentials are unavailable
