from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.url import (
    CreateURLRequest,
    URLResponse,
    URLListResponse,
    DeleteResponse
)
from app.services.url_service import (
    create_short_url,
    get_user_urls,
    soft_delete_url
)
from app.core.config import settings
from app.core.logging import logger

router = APIRouter(prefix="/links", tags=["Links"])

# ── Temporary auth helper ──────────────────────────────────────────
# This will be replaced by real JWT middleware in Auth Service (Step 5)
def get_current_user(
    x_user_id: str = Header(..., description="User ID"),
    x_user_plan: str = Header(default="free", description="User plan: free/paid/premium")
) -> dict:
    return {"user_id": x_user_id, "plan": x_user_plan}

# ── Endpoints ──────────────────────────────────────────────────────

@router.post(
    "",
    response_model=URLResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Shorten a URL",
    description="Creates a new short URL. Enforces plan limits."
)
async def shorten_url(
    request: CreateURLRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    logger.info(f"POST /links user={current_user['user_id']}")
    url = await create_short_url(
        db, request,
        current_user["user_id"],
        current_user["plan"]
    )
    return URLResponse(
        id=url.id,
        short_code=url.short_code,
        original_url=url.original_url,
        short_url=f"{settings.BASE_URL}/r/{url.short_code}",
        custom_alias=url.custom_alias,
        is_active=url.is_active,
        created_at=url.created_at
    )

@router.get(
    "",
    response_model=URLListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all links",
    description="Returns all active links for the current user."
)
async def list_urls(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    logger.info(f"GET /links user={current_user['user_id']}")
    urls, total = await get_user_urls(db, current_user["user_id"])
    return URLListResponse(
        total=total,
        links=[
            URLResponse(
                id=u.id,
                short_code=u.short_code,
                original_url=u.original_url,
                short_url=f"{settings.BASE_URL}/r/{u.short_code}",
                custom_alias=u.custom_alias,
                is_active=u.is_active,
                created_at=u.created_at
            )
            for u in urls
        ]
    )

@router.delete(
    "/{short_code}",
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a link",
    description="Soft deletes a link. Analytics history is preserved."
)
async def remove_url(
    short_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    logger.info(f"DELETE /links/{short_code} user={current_user['user_id']}")
    result = await soft_delete_url(db, short_code, current_user["user_id"])
    return DeleteResponse(**result)