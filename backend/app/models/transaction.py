from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import UUIDPK


class Transaction(UUIDPK, Base):
    __tablename__ = "transactions"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    security_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("securities.id", ondelete="RESTRICT")
    )
    txn_type: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    price: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    amount_native: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    fx_rate: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False, default=1)
    amount_cad: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String, nullable=False, default="manual")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
