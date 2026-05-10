from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import Timestamps, UUIDPK


class Account(UUIDPK, Timestamps, Base):
    __tablename__ = "accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    account_type: Mapped[str] = mapped_column(String, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CAD")
    institution: Mapped[str | None] = mapped_column(String)
    snaptrade_account_id: Mapped[str | None] = mapped_column(String, unique=True)
    is_synced: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
