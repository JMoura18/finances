from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import UUIDPK


class RiskSnapshot(UUIDPK, Base):
    __tablename__ = "risk_snapshots"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    regime: Mapped[str] = mapped_column(String, nullable=False)
    concentration: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    stress_results: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
