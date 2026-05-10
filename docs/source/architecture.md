# Architecture

```text
flowchart TD
    A[Upload audio] --> B[Normalize audio to mono 16kHz]
    B --> C[Chunk long recordings]
    C --> D{Transcription provider}
    D -->|Hosted| E[gpt-4o-mini-transcribe]
    D -->|Local| F[faster-whisper]
    E --> G[Merge transcript]
    F --> G
    G --> H{Notes provider}
    H -->|Hosted| I[gpt-5.4-mini]
    H -->|Local| J[Heuristic local notes]
    I --> K[Summary + notes + glossary + actions]
    J --> K
    K --> L[Cache result by file hash and settings]
    L --> M[Streamlit UI + CLI exports]
```

## Notes

- the UI is intentionally lightweight and portfolio-friendly
- the core logic lives in `src/quelque/`
- hosted mode is the primary fast path for demos
- local mode is the fallback for privacy or offline usage
