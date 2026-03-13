from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
import uuid

class CreateURLRequest(BaseModel):
    original_url: HttpUrl
    custom_alias: Optional[str] = None

class URLResponse(BaseModel):
    id: uuid.UUID
    short_code: str
    original_url: str
    short_url: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True