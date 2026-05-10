from __future__ import annotations

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import UUIDPK


class Security(UUIDPK, Base):
    __tablename__ = "securities"
    __table_args__ = (UniqueConstraint("symbol", "exchange"),)

    symbol: Mapped[str] = mapped_column(String, nullable=False)
    exchange: Mapped[str] = mapped_column(String, nullable=False)
    asset_class: Mapped[str] = mapped_column(String, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    name: Mapped[str | None] = mapped_column(String)
    sector: Mapped[str | None] = mapped_column(String)
    region: Mapped[str | None] = mapped_column(String)
