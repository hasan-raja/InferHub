from dataclasses import dataclass

import asyncpg
import clickhouse_connect
from aiokafka import AIOKafkaProducer
from redis.asyncio import Redis

from app.core.config import Settings
from app.db.schema import ensure_postgres_schema


@dataclass(slots=True)
class Dependencies:
    postgres: asyncpg.Pool
    redis: Redis
    clickhouse: object
    kafka_producer: AIOKafkaProducer


async def open_dependencies(settings: Settings) -> Dependencies:
    postgres = await asyncpg.create_pool(
        dsn=settings.postgres_dsn,
        min_size=1,
        max_size=5,
        command_timeout=5,
    )
    await ensure_postgres_schema(postgres)
    redis = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    clickhouse = clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
        database=settings.clickhouse_database,
    )
    kafka_producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        client_id="inferhub-gateway",
    )
    await kafka_producer.start()
    return Dependencies(
        postgres=postgres,
        redis=redis,
        clickhouse=clickhouse,
        kafka_producer=kafka_producer,
    )


async def close_dependencies(dependencies: Dependencies) -> None:
    await dependencies.kafka_producer.stop()
    await dependencies.redis.aclose()
    await dependencies.postgres.close()
    dependencies.clickhouse.close()
