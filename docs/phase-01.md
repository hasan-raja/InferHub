# Phase 1: Platform Bootstrap

## Architecture

Phase 1 establishes the control plane foundation for InferHub:

- FastAPI gateway with `/health`, `/ready` and `/metrics`
- typed config through environment variables
- PostgreSQL for durable platform metadata
- Redis for cache, rate-limit and ephemeral state in later phases
- ClickHouse for inference analytics
- Kafka topics for inference, billing and alert events
- Groq client scaffold for LLM, ASR, TTS and Vision calls
- floci documented as the AWS-compatible local cloud boundary

The gateway does not expose inference endpoints yet. That comes after gRPC worker contracts are introduced.

## File Placement

- `backend/app/main.py`: FastAPI app factory
- `backend/app/core/config.py`: environment-driven settings
- `backend/app/db/clients.py`: Postgres, Redis, ClickHouse and Kafka clients
- `backend/app/api/v1/health.py`: liveness and readiness endpoints
- `backend/app/integrations/groq_client.py`: Groq SDK adapter scaffold
- `infra/docker/postgres/001_schema.sql`: platform metadata schema
- `infra/docker/clickhouse/001_analytics.sql`: analytics event table
- `infra/docker/kafka/create-topics.sh`: Kafka topic bootstrap
- `docker-compose.yml`: local platform stack
- `infra/floci/*`: floci setup notes

## Local Commands

Optionally create an environment file for local overrides and your Groq key:

```bash
cp .env.example .env
```

Start dependencies and the gateway:

```bash
docker compose up --build
```

Check liveness:

```bash
curl -s http://localhost:8080/health | jq
```

Check dependency readiness:

```bash
curl -s http://localhost:8080/ready | jq
```

Open API docs:

```text
http://localhost:8080/docs
```

Prometheus scrape target:

```text
http://localhost:8080/metrics
```

## Groq Integration

Set `GROQ_API_KEY` in `.env`.

The scaffold in `backend/app/integrations/groq_client.py` wraps:

- chat completions
- streaming chat completions
- audio transcription
- text-to-speech
- vision-style chat completions with image messages

In Phase 2, each worker will own one modality and call this adapter behind gRPC service methods.

## floci Setup

Use floci as local AWS:

- object storage behaves like S3
- registry behaves like ECR
- credentials follow IAM-style environment variables
- k3d acts as the EKS-shaped runtime

The code should always use boto3-compatible clients with `endpoint_url` configured. That keeps migration to real AWS a config-only change.

## Testing

Phase 1 manual checks:

- `/health` returns `{"status": "ok"}`
- `/ready` returns all dependency checks as healthy once Compose is fully started
- `/metrics` exposes Prometheus metrics
- PostgreSQL contains platform tables
- ClickHouse contains `inferhub.inference_events`
- Kafka contains the four bootstrap topics

Automated tests will be added with the first business endpoints so test coverage maps to behavior, not only startup.

## Observability

This phase mounts Prometheus metrics at `/metrics` and instruments FastAPI with OpenTelemetry resource metadata.

Later phases will add:

- request counters and latency histograms
- worker failure counters
- active WebSocket gauges
- OTLP exporter configuration
- Grafana dashboards
- ClickHouse-backed analytics queries

## Sarvam API Team Alignment

This phase demonstrates the platform shape Sarvam cares about:

- Python and FastAPI service foundation
- production-style dependency readiness
- PostgreSQL, Redis, ClickHouse and Kafka integration points
- Groq as the model provider boundary
- observability hooks from day one
- AWS-compatible local cloud thinking through floci

It is intentionally small but serious: the next phases can add auth, gRPC workers, streaming APIs and rollout controls without changing the foundation.
