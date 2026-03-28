from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.url import URL
from app.services.cache_service import cache_service
from app.services.kafka_service import kafka_service
from app.core.exceptions import LinkNotFoundError, LinkInactiveError
from app.core.logging import logger
import asyncio

async def get_original_url(
    db: AsyncSession,
    short_code: str
) -> str:
    """
    Get original URL using cache-aside pattern.

    Flow:
    1. Check Redis cache
    2. Cache HIT  → return immediately
    3. Cache MISS → query PostgreSQL
    4. Store in Redis
    5. Return URL
    """

    # Step 1 — Check Redis cache first
    cached_url = await cache_service.get_url(short_code)
    if cached_url:
        logger.info(f"Cache HIT → redirecting {short_code}")
        return cached_url

    # Step 2 — Cache miss → query PostgreSQL
    logger.info(f"Cache MISS → querying DB for {short_code}")
    result = await db.execute(
        select(URL).where(
            URL.short_code == short_code,
        )
    )
    url = result.scalar_one_or_none()

    # Step 3 — Not found
    if not url:
        logger.warning(f"Link not found: {short_code}")
        raise LinkNotFoundError(short_code)

    # Step 4 — Found but deleted
    if url.deleted_at is not None:
        logger.warning(f"Link deleted: {short_code}")
        raise LinkNotFoundError(short_code)

    # Step 5 — Found but inactive
    if not url.is_active:
        logger.warning(f"Link inactive: {short_code}")
        raise LinkInactiveError(short_code)

    # Step 6 — Store in Redis cache for next time
    await cache_service.set_url(short_code, url.original_url)

    return url.original_url

async def process_click(
    short_code: str,
    user_id: str,
    ip_address: str,
    user_agent: str,
    referrer: str | None
) -> None:
    """
    Publish click event to Kafka asynchronously.
    Uses asyncio.create_task so redirect doesn't wait for Kafka.
    """
    asyncio.create_task(
        kafka_service.publish_click_event(
            short_code=short_code,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer
        )
    )