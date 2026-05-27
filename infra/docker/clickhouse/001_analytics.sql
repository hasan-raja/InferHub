CREATE DATABASE IF NOT EXISTS inferhub;

CREATE TABLE IF NOT EXISTS inferhub.inference_events (
    event_time DateTime64(3) DEFAULT now64(),
    request_id String,
    user_id String,
    modality LowCardinality(String),
    model LowCardinality(String),
    provider LowCardinality(String),
    status LowCardinality(String),
    latency_ms UInt32,
    cache_hit UInt8,
    worker_name LowCardinality(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_time)
ORDER BY (event_time, modality, model, status);

