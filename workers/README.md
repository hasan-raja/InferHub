# Workers

Phase 3 adds modality-specific gRPC workers:

- `llm-worker`
- `asr-worker`
- `tts-worker`
- `vision-worker`

Each worker wraps Groq, exposes a gRPC service, serves `/health` and `/metrics`, tracks latency, normalizes responses and retries transient provider failures.

Local ports:

- LLM gRPC: `50051`, health: `8091`
- ASR gRPC: `50052`, health: `8092`
- TTS gRPC: `50053`, health: `8093`
- Vision gRPC: `50054`, health: `8094`

