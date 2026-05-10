from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import UUIDPK


class NewsItem(UUIDPK, Base):
    __tablename__ = "news_items"

    security_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("securities.id", ondelete="CASCADE")
    )
    headline: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    relevance: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    sentiment: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    summary: Mapped[str | None] = mapped_column(Text)
