# InferHub

Unified multimodal AI inference platform exposing LLM, ASR, TTS and Vision through low-latency APIs with streaming, observability and rollout controls.

Phase 1 creates the production-shaped foundation:

- FastAPI API gateway bootstrap
- typed configuration
- PostgreSQL, Redis, ClickHouse and Kafka local dependencies
- health and readiness endpoints
- Groq integration scaffold
- Docker Compose and floci local cloud notes

See [docs/phase-01.md](docs/phase-01.md) for architecture, commands and Sarvam alignment.
See [docs/phase-02.md](docs/phase-02.md) for authentication, authorization, rate limiting and model registry.
