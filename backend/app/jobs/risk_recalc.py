"""Weekly risk recalculation.

For every user, derive holdings, compute concentration + stress, persist a
RiskSnapshot, generate alerts. Cron-friendly entry point.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import SessionLocal
from app.models import (
    Account,
    Alert,
    Holding,
    Price,
    RiskSnapshot,
    Security,
    User,
)
from app.services.alerts import evaluate_alerts
from app.services.risk_scorer import (
    HoldingValuation,
    composite_score,
    score_concentration,
    stress_test,
)


async def _holdings_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[HoldingValuation]:
    rows = await db.execute(
        select(Holding, Security, Price.close)
        .join(Account, Account.id == Holding.account_id)
        .join(Security, Security.id == Holding.security_id)
        .join(Price, Price.security_id == Holding.security_id, isouter=True)
        .where(Account.user_id == user_id)
        .order_by(Price.as_of.desc().nullslast())
    )
    seen: set[uuid.UUID] = set()
    out: list[HoldingValuation] = []
    for h, sec, close in rows.all():
        if h.id in seen:
            continue
        seen.add(h.id)
        px = Decimal(close) if close is not None else Decimal(0)
        out.append(HoldingValuation(
            symbol=sec.symbol,
            sector=sec.sector,
            region=sec.region,
            asset_class=sec.asset_class,
            market_value_cad=float(h.quantity * px),
        ))
    return out


async def recalc_user(
    db: AsyncSession, user: User, regime: str = "normal"
) -> RiskSnapshot | None:
    holdings = await _holdings_for_user(db, user.id)
    if not holdings:
        return None
    concentration = score_concentration(holdings)
    stresses = stress_test(holdings)
    score = composite_score(concentration, stresses)

    snap = RiskSnapshot(
        user_id=user.id,
        score=Decimal(str(score)),
        regime=regime,
        concentration=concentration,
        stress_results=stresses,
    )
    db.add(snap)

    candidates = evaluate_alerts(score, regime, concentration, stresses)
    if candidates:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        existing_rows = await db.execute(
            select(Alert).where(Alert.user_id == user.id, Alert.created_at >= cutoff)
        )
        existing_keys = {
            (a.category, a.title) for a in existing_rows.scalars().all()
        }
        for c in candidates:
            if (c.category, c.title) in existing_keys:
                continue
            db.add(Alert(
                user_id=user.id,
                severity=c.severity,
                title=c.title,
                body=c.body,
                category=c.category,
            ))

    return snap


async def recalc_all_users() -> int:
    """Recalc every user. Returns count of snapshots written."""
    written = 0
    async with SessionLocal() as db:
        rows = await db.execute(select(User))
        for user in rows.scalars().all():
            snap = await recalc_user(db, user)
            if snap is not None:
                written += 1
        await db.commit()
    return written
