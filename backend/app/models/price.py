from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import UUIDPK


class Price(UUIDPK, Base):
    __tablename__ = "prices"
    __table_args__ = (UniqueConstraint("security_id", "as_of"),)

    security_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("securities.id", ondelete="CASCADE"), nullable=False
    )
    as_of: Mapped[date] = mapped_column(Date, nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False, default="yahoo")
