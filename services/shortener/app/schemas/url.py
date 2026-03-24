from pydantic import BaseModel, HttpUrl, Field, field_validator
from typing import Optional
from datetime import datetime
import uuid
import re

ALIAS_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

class CreateURLRequest(BaseModel):
    original_url: HttpUrl = Field(
        ...,
        description="The full URL to shorten",
        examples=["https://www.google.com"]
    )
    custom_alias: Optional[str] = Field(
        None,
        min_length=3,
        max_length=50,
        description="Optional custom alias (Paid/Premium only)"
    )

    @field_validator("custom_alias")
    @classmethod
    def validate_alias(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not ALIAS_PATTERN.match(v):
            raise ValueError(
                "Alias can only contain letters, numbers, hyphens and underscores."
            )
        return v.lower()  # always store lowercase

class URLResponse(BaseModel):
    id: uuid.UUID
    short_code: str
    original_url: str
    short_url: str
    custom_alias: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class URLListResponse(BaseModel):
    total: int
    links: list[URLResponse]

class DeleteResponse(BaseModel):
    message: str
    short_code: str