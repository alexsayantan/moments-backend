from datetime import datetime, timezone
from sqlmodel import Field, SQLModel
from sqlalchemy import DateTime
import uuid


def generate_uuid7() -> uuid.UUID:
    """Generate a time-ordered UUIDv7 (RFC 9562).

    Uses Python 3.14+ native uuid.uuid7() if available, with a standards-compliant
    fallback for older runtimes.
    """
    if hasattr(uuid, "uuid7"):
        return uuid.uuid7()

    # Fallback RFC 9562 UUIDv7 generator
    import os
    import time

    timestamp_ms = time.time_ns() // 1_000_000
    rand_bytes = bytearray(os.urandom(10))
    b = bytearray(16)
    b[0] = (timestamp_ms >> 40) & 0xFF
    b[1] = (timestamp_ms >> 32) & 0xFF
    b[2] = (timestamp_ms >> 24) & 0xFF
    b[3] = (timestamp_ms >> 16) & 0xFF
    b[4] = (timestamp_ms >> 8) & 0xFF
    b[5] = timestamp_ms & 0xFF
    b[6] = (0x70 | (rand_bytes[0] & 0x0F))  # version 7
    b[7] = rand_bytes[1]
    b[8] = (0x80 | (rand_bytes[2] & 0x3F))  # variant RFC 4122
    b[9:16] = rand_bytes[3:10]
    return uuid.UUID(bytes=bytes(b))


class BaseAuditModel(SQLModel):
    """Base model with a time-ordered UUIDv7 primary key and UTC audit timestamps.

    Inherited by domain models to ensure consistent primary keys and timestamps
    across all tables.
    """

    id: uuid.UUID = Field(
        default_factory=generate_uuid7,
        primary_key=True,
        index=True,
        nullable=False,
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
        nullable=False,
    )
