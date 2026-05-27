# Phase 4: Gateway APIs and Streaming

## Architecture

Phase 4 exposes the client-facing InferHub API surface:

- `POST /v1/llm/chat`
- `POST /v1/asr/transcribe`
- `POST /v1/tts/synthesize`
- `POST /v1/vision/analyze`
- `WS /ws/llm`
- `WS /ws/asr`

The gateway validates requests, authenticates API keys, rate limits with Redis, calls the correct gRPC worker and normalizes responses for clients.

## Routing

Client calls never reach Groq directly:

```text
Client -> FastAPI Gateway -> gRPC Worker -> Groq SDK -> Groq API
```

Worker targets are configured with:

```env
LLM_WORKER_TARGET=llm-worker:50051
ASR_WORKER_TARGET=asr-worker:50052
TTS_WORKER_TARGET=tts-worker:50053
VISION_WORKER_TARGET=vision-worker:50054
```

## Local Commands

Start the full stack:

```bash
docker compose up --build
```

Create or reuse an admin API key:

```bash
docker compose exec gateway python -m app.scripts.create_admin_key
export INFERHUB_KEY="paste-key-here"
```

LLM:

```bash
curl -s http://localhost:8080/v1/llm/chat \
  -H "Authorization: Bearer $INFERHUB_KEY" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Say hello from InferHub"}]}' \
  | python3 -m json.tool
```

LLM server-sent token stream:

```bash
curl -N http://localhost:8080/v1/llm/chat \
  -H "Authorization: Bearer $INFERHUB_KEY" \
  -H "Content-Type: application/json" \
  -d '{"stream":true,"messages":[{"role":"user","content":"Stream a short answer"}]}'
```

ASR:

```bash
curl -s http://localhost:8080/v1/asr/transcribe \
  -H "Authorization: Bearer $INFERHUB_KEY" \
  -F "file=@sample.wav" \
  -F "model=whisper-large-v3-turbo" \
  | python3 -m json.tool
```

TTS:

```bash
curl -s http://localhost:8080/v1/tts/synthesize \
  -H "Authorization: Bearer $INFERHUB_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text":"InferHub text to speech is online","voice":"Fritz-PlayAI"}' \
  --output speech.wav
```

Vision:

```bash
IMAGE_B64="$(base64 -w 0 sample.png)"

curl -s http://localhost:8080/v1/vision/analyze \
  -H "Authorization: Bearer $INFERHUB_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"Describe the image\",\"images\":[{\"mime_type\":\"image/png\",\"content_base64\":\"$IMAGE_B64\"}]}" \
  | python3 -m json.tool
```

## WebSockets

LLM WebSocket:

```text
ws://localhost:8080/ws/llm?api_key=<key>
```

Send JSON:

```json
{
  "messages": [{"role": "user", "content": "Stream one sentence"}],
  "model": "llama-3.3-70b-versatile"
}
```

ASR WebSocket:

```text
ws://localhost:8080/ws/asr?api_key=<key>&model=whisper-large-v3-turbo
```

Send audio bytes. The gateway forwards each audio message to the ASR worker and emits partial transcript messages from the normalized transcript. A later phase can replace this with true chunk-level ASR when the provider supports streaming transcription.

Redis tracks WebSocket presence using:

```text
ws:llm:<connection_id>
ws:asr:<connection_id>
ws:llm:active
ws:asr:active
```

## Error Handling

The gateway maps worker gRPC failures to API responses:

- `INVALID_ARGUMENT` -> `422`
- `DEADLINE_EXCEEDED` -> `504`
- `UNAVAILABLE` -> `503`
- other worker failures -> `502`

If Groq returns `NotFoundError`, verify the model is available to your Groq project:

```bash
curl -s https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  | python3 -m json.tool
```

Then call InferHub with one of the returned model IDs:

```bash
curl -s http://localhost:8080/v1/llm/chat \
  -H "Authorization: Bearer $INFERHUB_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":"Say hello from InferHub"}]}' \
  | python3 -m json.tool
```

## Sarvam Alignment

This phase demonstrates the API-team surface area Sarvam expects:

- production FastAPI inference endpoints
- authenticated, rate-limited client access
- gRPC routing to model-family workers
- streaming LLM responses
- WebSocket connection management
- Redis-backed realtime presence
- normalized provider responses and gateway error handling
