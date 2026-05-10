from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import UUIDPK


class ContributionRoom(UUIDPK, Base):
    __tablename__ = "contribution_rooms"
    __table_args__ = (UniqueConstraint("user_id", "account_type", "tax_year"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    account_type: Mapped[str] = mapped_column(String, nullable=False)
    tax_year: Mapped[int] = mapped_column(Integer, nullable=False)
    total_room_cad: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    used_cad: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False, default=0)
