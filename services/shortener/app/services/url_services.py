import random
import string
from sqlalchemy.orm import Session
from app.models.url import URL
from app.schemas.url import CreateURLRequest
from app.core.config import settings
from fastapi import HTTPException

CHARACTERS = string.ascii_letters + string.digits  # Base62

def generate_short_code(length: int = 6) -> str:
    return ''.join(random.choices(CHARACTERS, k=length))

def create_short_url(db: Session, request: CreateURLRequest, user_id: str, user_plan: str):
    # Plan check — Free users max 5 links
    if user_plan == "free":
        count = db.query(URL).filter(
            URL.user_id == user_id,
            URL.deleted_at == None
        ).count()
        if count >= 5:
            raise HTTPException(
                status_code=403,
                detail="Link limit reached. Upgrade to Paid for unlimited links."
            )

    # Custom alias check — Paid and Premium only
    if request.custom_alias:
        if user_plan == "free":
            raise HTTPException(
                status_code=403,
                detail="Custom aliases require a Paid plan."
            )
        # Check alias not already taken
        existing = db.query(URL).filter(URL.short_code == request.custom_alias).first()
        if existing:
            raise HTTPException(status_code=409, detail="This alias is already taken.")
        short_code = request.custom_alias
    else:
        # Generate unique short code
        while True:
            short_code = generate_short_code()
            existing = db.query(URL).filter(URL.short_code == short_code).first()
            if not existing:
                break

    url = URL(
        short_code=short_code,
        original_url=str(request.original_url),
        user_id=user_id,
        custom_alias=request.custom_alias,
    )
    db.add(url)
    db.commit()
    db.refresh(url)
    return url

def get_user_urls(db: Session, user_id: str):
    return db.query(URL).filter(
        URL.user_id == user_id,
        URL.deleted_at == None
    ).all()

def delete_url(db: Session, short_code: str, user_id: str):
    url = db.query(URL).filter(
        URL.short_code == short_code,
        URL.user_id == user_id
    ).first()
    if not url:
        raise HTTPException(status_code=404, detail="Link not found.")
    from datetime import datetime, timezone
    url.deleted_at = datetime.now(timezone.utc)
    url.is_active = False
    db.commit()
    return {"message": "Link deleted successfully."}