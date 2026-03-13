from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.url import CreateURLRequest, URLResponse
from app.services.url_service import create_short_url, get_user_urls, delete_url
from app.core.config import settings
from typing import List
import uuid

router = APIRouter(prefix="/links", tags=["links"])

# Temporary helper — will be replaced by real JWT auth later
def get_current_user(x_user_id: str = Header(...), x_user_plan: str = Header(default="free")):
    return {"user_id": x_user_id, "plan": x_user_plan}

@router.post("", response_model=URLResponse, status_code=201)
def shorten_url(
    request: CreateURLRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    url = create_short_url(db, request, current_user["user_id"], current_user["plan"])
    return {**url.__dict__, "short_url": f"{settings.BASE_URL}/r/{url.short_code}"}

@router.get("", response_model=List[URLResponse])
def list_urls(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    urls = get_user_urls(db, current_user["user_id"])
    return [{**u.__dict__, "short_url": f"{settings.BASE_URL}/r/{u.short_code}"} for u in urls]

@router.delete("/{short_code}", status_code=200)
def remove_url(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return delete_url(db, short_code, current_user["user_id"])