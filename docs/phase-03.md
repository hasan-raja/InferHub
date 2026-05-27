# Phase 3: gRPC Workers and Groq Integration

## Architecture

Phase 3 introduces production-shaped inference workers behind the gateway:

- `llm-worker`: Groq chat completions and token streaming
- `asr-worker`: Groq speech-to-text
- `tts-worker`: Groq text-to-speech
- `vision-worker`: Groq image analysis

Each worker runs:

- a gRPC server for gateway-to-worker traffic
- an HTTP health sidecar with `/health` and `/metrics`
- a shared Groq provider adapter
- retry handling with exponential backoff
- latency histograms and request counters
- normalized response messages defined by protobuf

## File Placement

- `proto/inferhub/v1/inference.proto`: worker gRPC contract
- `workers/Dockerfile`: shared worker image
- `workers/requirements.txt`: worker runtime dependencies
- `workers/common/runner.py`: gRPC plus HTTP health runtime
- `workers/common/provider.py`: Groq SDK adapter and response normalization helpers
- `workers/llm_worker/service.py`: chat and streaming chat worker
- `workers/asr_worker/service.py`: transcription worker
- `workers/tts_worker/service.py`: speech synthesis worker
- `workers/vision_worker/service.py`: image analysis worker
- `docker-compose.yml`: worker service definitions

## Local Commands

Set your Groq key in `.env`:

```bash
cp .env.example .env
# edit GROQ_API_KEY=...
```

Build and run the platform:

```bash
docker compose up --build
```

Health checks:

```bash
curl -s http://localhost:8091/health | python3 -m json.tool
curl -s http://localhost:8092/health | python3 -m json.tool
curl -s http://localhost:8093/health | python3 -m json.tool
curl -s http://localhost:8094/health | python3 -m json.tool
```

Metrics:

```bash
curl -s http://localhost:8091/metrics
```

The gRPC ports are:

- `localhost:50051` for LLM
- `localhost:50052` for ASR
- `localhost:50053` for TTS
- `localhost:50054` for Vision

## Groq Integration

Workers use `AsyncGroq` through `workers/common/provider.py`.

Provider calls are isolated behind modality-specific methods:

- `chat`
- `stream_chat`
- `transcribe`
- `synthesize`
- `analyze_vision`

This keeps Groq-specific response formats out of the gateway and gives each worker one place to normalize provider output.

## Testing

Validate Python syntax and Compose:

```bash
python3 -m compileall backend workers
docker compose config --quiet
```

Run unit tests:

```bash
docker compose build gateway
docker run --rm \
  -v /mnt/f/claude-code/inferhub/tests:/app/tests:ro \
  inferhub-gateway pytest /app/tests
```

Build worker image:

```bash
docker compose build llm-worker
```

## Sarvam Alignment

This phase maps strongly to Sarvam API Team expectations:

- gRPC service boundaries between gateway and inference workers
- separate workers for model families and modalities
- real Groq SDK integration for LLM, ASR, TTS and Vision
- streaming support for low-latency token delivery
- retry and latency tracking around provider calls
- health and Prometheus metrics for each worker
- Dockerized microservices ready for Kubernetes deployment in a later phase

