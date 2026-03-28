from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.services.redirect_service import get_original_url, process_click
from app.services.cache_service import cache_service
from app.core.logging import logger

router = APIRouter(tags=["Redirect"])

@router.get(
    "/r/{short_code}",
    status_code=status.HTTP_302_FOUND,
    summary="Redirect to original URL",
    description="Resolves short code and redirects. Checks Redis cache first."
)
async def redirect_url(
    short_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # Extract request metadata for analytics
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    referrer = request.headers.get("referer", None)

    # Get user_id from header if available (set by API Gateway later)
    user_id = request.headers.get("x-user-id", "anonymous")

    logger.info(f"Redirect request for {short_code} from {ip_address}")

    # Get original URL (cache-aside pattern)
    original_url = await get_original_url(db, short_code)

    # Publish click event to Kafka (non-blocking)
    await process_click(
        short_code=short_code,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        referrer=referrer
    )

    logger.info(f"Redirecting {short_code} → {original_url}")

    # Return 302 redirect
    return RedirectResponse(
        url=original_url,
        status_code=status.HTTP_302_FOUND
    )

@router.get(
    "/health",
    tags=["Health"],
    summary="Health check"
)
async def health():
    cache_stats = await cache_service.get_cache_stats()
    return {
        "status": "ok",
        "service": "Redirect Service",
        "version": "1.0.0",
        "cache": cache_stats
    }