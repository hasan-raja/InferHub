# Phase 2: Auth, Security and Model Registry

## Architecture

Phase 2 adds the API platform security boundary:

- Bearer API key authentication using HMAC-SHA256 hashes with an environment pepper
- role-based authorization for `free`, `enterprise` and `admin`
- Redis fixed-window rate limiting per API key
- model registry APIs backed by PostgreSQL
- secure request middleware for request IDs, body limits and security headers
- health checks for auth tables and model registry state

## Local Commands

Rebuild after code changes:

```bash
docker compose up --build
```

Create the first admin key inside the gateway container:

```bash
docker compose exec gateway python -m app.scripts.create_admin_key
```

Save the printed `api_key` for local testing.

Validate the key:

```bash
export INFERHUB_KEY="paste-key-here"

curl -s http://localhost:8080/v1/auth/api-keys/validate \
  -H "Authorization: Bearer $INFERHUB_KEY" | jq
```

List active models:

```bash
curl -s http://localhost:8080/v1/models \
  -H "Authorization: Bearer $INFERHUB_KEY" | jq
```

Create another API key as admin:

```bash
curl -s http://localhost:8080/v1/auth/api-keys \
  -X POST \
  -H "Authorization: Bearer $INFERHUB_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"dev@inferhub.local","role":"free","name":"dev-key"}' | jq
```

Run unit tests locally:

```bash
pip install -r backend/requirements.txt
pytest
```

Or with the gateway image:

```bash
docker compose build gateway
docker run --rm \
  -v /mnt/f/claude-code/inferhub/tests:/app/tests:ro \
  inferhub-gateway pytest /app/tests
```

## API Surface

- `POST /v1/auth/api-keys`: admin-only key creation
- `GET /v1/auth/api-keys/validate`: validate current key and consume rate limit
- `DELETE /v1/auth/api-keys/{api_key_id}`: admin-only revocation
- `GET /v1/models`: authenticated model registry listing
- `POST /v1/models`: admin-only model registration
- `PATCH /v1/models/{model_id}`: admin-only model state update
- `GET /health/security`: auth and model registry health summary

## Sarvam Alignment

This phase maps directly to API-team backend expectations:

- API key authentication and secure secret handling
- role-based authorization for platform tiers
- Redis-backed per-key rate limiting with `429` behavior
- production-shaped model registry for routing future inference traffic
- health endpoints that surface security and registry readiness
- unit tests for auth primitives and rate limiting
