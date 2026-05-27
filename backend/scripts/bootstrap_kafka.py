import asyncio

from aiokafka.admin import AIOKafkaAdminClient, NewTopic

from app.core.config import get_settings


TOPICS = [
    "inference.requests",
    "inference.completed",
    "billing.events",
    "alerts.events",
]


async def main() -> None:
    settings = get_settings()
    admin = AIOKafkaAdminClient(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        client_id="inferhub-topic-bootstrap",
    )
    await admin.start()
    try:
        existing = await admin.list_topics()
        topics = [
            NewTopic(name=topic, num_partitions=3, replication_factor=1)
            for topic in TOPICS
            if topic not in existing
        ]
        if topics:
            await admin.create_topics(topics)
    finally:
        await admin.close()


if __name__ == "__main__":
    asyncio.run(main())

