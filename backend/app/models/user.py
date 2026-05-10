from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import Timestamps, UUIDPK


class User(UUIDPK, Timestamps, Base):
    __tablename__ = "users"

    firebase_uid: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String)
    province: Mapped[str | None] = mapped_column(String)
    birth_year: Mapped[int | None] = mapped_column(Integer)
