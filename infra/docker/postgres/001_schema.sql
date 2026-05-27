CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('free', 'enterprise', 'admin')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    key_hash TEXT UNIQUE NOT NULL,
    key_prefix TEXT,
    name TEXT NOT NULL,
    last_used_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS quotas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    requests_per_minute INTEGER NOT NULL,
    tokens_per_day BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_quotas_user_id ON quotas (user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash_active ON api_keys (key_hash) WHERE revoked_at IS NULL;

CREATE TABLE IF NOT EXISTS request_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id TEXT UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id),
    modality TEXT NOT NULL,
    model TEXT NOT NULL,
    status TEXT NOT NULL,
    latency_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS worker_health (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    worker_name TEXT NOT NULL,
    modality TEXT NOT NULL,
    status TEXT NOT NULL,
    latency_ms INTEGER,
    active_requests INTEGER NOT NULL DEFAULT 0,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS feature_flags (
    name TEXT PRIMARY KEY,
    enabled BOOLEAN NOT NULL DEFAULT false,
    rules JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS deployments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name TEXT NOT NULL,
    stable_weight INTEGER NOT NULL DEFAULT 100,
    canary_weight INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS model_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    family TEXT NOT NULL DEFAULT 'unknown',
    modality TEXT NOT NULL,
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT true,
    active BOOLEAN NOT NULL DEFAULT true,
    supports_streaming BOOLEAN NOT NULL DEFAULT false,
    priority INTEGER NOT NULL DEFAULT 100,
    health TEXT NOT NULL DEFAULT 'unknown',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (provider, model_name)
);

INSERT INTO feature_flags (name, enabled)
VALUES
    ('enable_llm_streaming', true),
    ('enable_vision_beta', false),
    ('enable_metrics', true)
ON CONFLICT (name) DO NOTHING;

INSERT INTO model_registry
    (family, modality, provider, model_name, enabled, active, supports_streaming, priority, health)
VALUES
    ('llama', 'llm', 'groq', 'llama-3.3-70b-versatile', true, true, true, 10, 'healthy'),
    ('qwen', 'llm', 'groq', 'qwen/qwen3-32b', true, true, true, 20, 'healthy'),
    ('whisper', 'asr', 'groq', 'whisper-large-v3-turbo', true, true, false, 10, 'healthy'),
    ('groq-tts', 'tts', 'groq', 'playai-tts', true, true, false, 10, 'healthy'),
    ('vision', 'vision', 'groq', 'meta-llama/llama-4-scout-17b-16e-instruct', true, true, false, 10, 'healthy')
ON CONFLICT (provider, model_name) DO NOTHING;
