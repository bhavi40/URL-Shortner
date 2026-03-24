import random
import string
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone

from app.models.url import URL
from app.schemas.url import CreateURLRequest
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import (
    LinkNotFoundError,
    LinkLimitReachedError,
    CustomAliasNotAllowedError,
    AliasAlreadyTakenError,
    ShortCodeGenerationError
)

CHARACTERS = string.ascii_letters + string.digits  # Base62

def _generate_short_code(length: int) -> str:
    """Generate a random Base62 short code."""
    return ''.join(random.choices(CHARACTERS, k=length))

async def _is_short_code_taken(db: AsyncSession, code: str) -> bool:
    """Check if a short code already exists in DB."""
    result = await db.execute(
        select(URL.id).where(URL.short_code == code).limit(1)
    )
    return result.scalar_one_or_none() is not None

async def _enforce_plan_limits(
    db: AsyncSession,
    user_id: str,
    user_plan: str,
    custom_alias: str | None
) -> None:
    """Enforce business rules based on user plan."""

    # Free plan: max link limit
    if user_plan == "free":
        result = await db.execute(
            select(func.count(URL.id)).where(
                URL.user_id == user_id,
                URL.deleted_at.is_(None)
            )
        )
        count = result.scalar() or 0
        logger.info(f"User {user_id} has {count} active links (plan: free)")
        if count >= settings.FREE_PLAN_MAX_LINKS:
            raise LinkLimitReachedError()

    # Custom alias: Paid and Premium only
    if custom_alias and user_plan == "free":
        raise CustomAliasNotAllowedError()

async def _get_unique_short_code(db: AsyncSession) -> str:
    """Generate a unique short code with collision handling."""
    for attempt in range(settings.MAX_RETRIES_SHORT_CODE):
        code = _generate_short_code(settings.SHORT_CODE_LENGTH)
        if not await _is_short_code_taken(db, code):
            logger.debug(f"Generated short code '{code}' on attempt {attempt + 1}")
            return code
    logger.error("Failed to generate unique short code after max retries")
    raise ShortCodeGenerationError()

async def create_short_url(
    db: AsyncSession,
    request: CreateURLRequest,
    user_id: str,
    user_plan: str
) -> URL:
    """Create a new short URL with plan enforcement."""
    logger.info(f"Creating short URL for user {user_id} (plan: {user_plan})")

    # Enforce plan limits
    await _enforce_plan_limits(db, user_id, user_plan, request.custom_alias)

    # Determine short code
    if request.custom_alias:
        if await _is_short_code_taken(db, request.custom_alias):
            raise AliasAlreadyTakenError(request.custom_alias)
        short_code = request.custom_alias
    else:
        short_code = await _get_unique_short_code(db)

    # Create record
    url = URL(
        short_code=short_code,
        original_url=str(request.original_url),
        user_id=user_id,
        custom_alias=request.custom_alias,
    )
    db.add(url)
    await db.flush()   # write to DB but don't commit yet
    await db.refresh(url)

    logger.info(f"Created short URL '{short_code}' for user {user_id}")
    return url

async def get_user_urls(
    db: AsyncSession,
    user_id: str
) -> tuple[list[URL], int]:
    """Get all active links for a user with total count."""
    result = await db.execute(
        select(URL).where(
            URL.user_id == user_id,
            URL.deleted_at.is_(None)
        ).order_by(URL.created_at.desc())
    )
    urls = result.scalars().all()
    return urls, len(urls)

async def get_url_by_code(
    db: AsyncSession,
    short_code: str,
    user_id: str
) -> URL:
    """Get a specific link owned by a user."""
    result = await db.execute(
        select(URL).where(
            URL.short_code == short_code,
            URL.user_id == user_id,
            URL.deleted_at.is_(None)
        )
    )
    url = result.scalar_one_or_none()
    if not url:
        raise LinkNotFoundError(short_code)
    return url

async def soft_delete_url(
    db: AsyncSession,
    short_code: str,
    user_id: str
) -> dict:
    """Soft delete a link — marks as deleted, preserves analytics."""
    url = await get_url_by_code(db, short_code, user_id)
    url.deleted_at = datetime.now(timezone.utc)
    url.is_active = False
    await db.flush()
    logger.info(f"Soft deleted link '{short_code}' for user {user_id}")
    return {"message": "Link deleted successfully.", "short_code": short_code}