"""SQLAlchemy ORM models for caching service."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class TransformCache(Base):
    """
    Cache for transformer function results.
    
    Stores the mapping from input strings to their transformed outputs,
    avoiding redundant calls to the (simulated) external transformer service.
    """

    __tablename__ = "transform_cache"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    input_string: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True, index=True
    )
    transformed_string: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<TransformCache(input='{self.input_string[:20]}...', transformed='{self.transformed_string[:20]}...')>"


class Payload(Base):
    """
    Stores generated payloads with their identifiers.
    
    Uses deterministic SHA-256 hash of inputs as the ID, ensuring identical
    inputs always produce the same payload ID for true idempotency.
    """

    __tablename__ = "payloads"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True
    )
    # SHA256 hash of canonical JSON representation of inputs for deduplication
    input_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    # Store original inputs for debugging/auditing purposes
    list1_json: Mapped[str] = mapped_column(Text, nullable=False)
    list2_json: Mapped[str] = mapped_column(Text, nullable=False)
    # The final interleaved output string
    output: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Composite index for potential future queries by creation time
    __table_args__ = (Index("ix_payloads_created_at", "created_at"),)

    def __repr__(self) -> str:
        return f"<Payload(id={self.id}, output='{self.output[:30]}...')>"

