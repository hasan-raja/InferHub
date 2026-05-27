import asyncio
import os

import asyncpg

from app.auth.models import ApiKeyCreateRequest
from app.auth.service import create_api_key
from app.core.config import get_settings


async def main() -> None:
    settings = get_settings()
    email = os.environ.get("ADMIN_EMAIL", "admin@inferhub.local")
    name = os.environ.get("ADMIN_KEY_NAME", "local-admin")
    pool = await asyncpg.create_pool(settings.postgres_dsn, min_size=1, max_size=2)
    try:
        response = await create_api_key(
            pool,
            settings,
            ApiKeyCreateRequest(
                email=email,
                role="admin",
                name=name,
                requests_per_minute=settings.default_admin_rpm,
                tokens_per_day=10_000_000,
            ),
        )
    finally:
        await pool.close()

    print("Store this API key now; it is shown once.")
    print(f"api_key={response.api_key}")
    print(f"api_key_id={response.api_key_id}")
    print(f"user_id={response.user_id}")


if __name__ == "__main__":
    asyncio.run(main())

