import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.database import Base

class URL(Base):
    """
    Read-only model — Redirect Service only reads from this table.
    Shortener Service owns writes.
    """
    __tablename__ = "urls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    short_code = Column(String(50), unique=True, nullable=False)
    original_url = Column(Text, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    custom_alias = Column(String(50), unique=True, nullable=True)
    branded_domain = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_urls_short_code", "short_code"),
    )

    def __repr__(self):
        return f"<URL short_code={self.short_code}>"