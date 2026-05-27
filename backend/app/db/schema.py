import asyncpg


MODEL_SEEDS = [
    ("llama", "llm", "groq", "llama-3.3-70b-versatile", True, True, 10, "healthy"),
    ("qwen", "llm", "groq", "qwen/qwen3-32b", True, True, 20, "healthy"),
    ("whisper", "asr", "groq", "whisper-large-v3-turbo", True, False, 10, "healthy"),
    ("groq-tts", "tts", "groq", "playai-tts", True, False, 10, "healthy"),
    ("vision", "vision", "groq", "meta-llama/llama-4-scout-17b-16e-instruct", True, False, 10, "healthy"),
]


async def ensure_postgres_schema(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
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
                name TEXT NOT NULL,
                last_used_at TIMESTAMPTZ,
                revoked_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );

            ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS key_prefix TEXT;
            CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash_active ON api_keys (key_hash) WHERE revoked_at IS NULL;

            CREATE TABLE IF NOT EXISTS quotas (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID NOT NULL REFERENCES users(id),
                requests_per_minute INTEGER NOT NULL,
                tokens_per_day BIGINT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_quotas_user_id ON quotas (user_id);

            CREATE TABLE IF NOT EXISTS model_registry (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                modality TEXT NOT NULL,
                provider TEXT NOT NULL,
                model_name TEXT NOT NULL,
                enabled BOOLEAN NOT NULL DEFAULT true,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                UNIQUE (provider, model_name)
            );

            ALTER TABLE model_registry ADD COLUMN IF NOT EXISTS family TEXT NOT NULL DEFAULT 'unknown';
            ALTER TABLE model_registry ADD COLUMN IF NOT EXISTS active BOOLEAN NOT NULL DEFAULT true;
            ALTER TABLE model_registry ADD COLUMN IF NOT EXISTS supports_streaming BOOLEAN NOT NULL DEFAULT false;
            ALTER TABLE model_registry ADD COLUMN IF NOT EXISTS priority INTEGER NOT NULL DEFAULT 100;
            ALTER TABLE model_registry ADD COLUMN IF NOT EXISTS health TEXT NOT NULL DEFAULT 'unknown';
            UPDATE model_registry SET active = enabled WHERE active IS DISTINCT FROM enabled;
            """
        )
        await conn.executemany(
            """
            INSERT INTO model_registry
                (family, modality, provider, model_name, active, enabled, supports_streaming, priority, health)
            VALUES ($1, $2, $3, $4, $5, $5, $6, $7, $8)
            ON CONFLICT (provider, model_name) DO UPDATE SET
                family = EXCLUDED.family,
                modality = EXCLUDED.modality,
                active = EXCLUDED.active,
                enabled = EXCLUDED.enabled,
                supports_streaming = EXCLUDED.supports_streaming,
                priority = EXCLUDED.priority,
                health = EXCLUDED.health
            """,
            MODEL_SEEDS,
        )

