# Workers

Phase 2 will add modality-specific gRPC workers:

- `llm-worker`
- `asr-worker`
- `tts-worker`
- `vision-worker`

Each worker will wrap the shared Groq integration pattern, expose health, emit metrics and normalize responses.

