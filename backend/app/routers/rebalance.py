from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, CurrentUserDep
from app.database import get_db
from app.models import Account, Holding, Price, Security
from app.services.rebalancer import HoldingForRebalance, plan

router = APIRouter()


class RebalanceSuggestion(BaseModel):
    asset_class: str
    current_weight: float
    target_weight: float
    drift: float
    action: str


class ActionOut(BaseModel):
    account: str
    action: str
    symbol: str | None
    amount_cad: float
    reason: str


class RebalancePlan(BaseModel):
    suggestions: list[RebalanceSuggestion]
    actions: list[ActionOut]


# Default target — user-editable later
TARGET = {
    "etf": 0.55,
    "equity": 0.20,
    "reit": 0.05,
    "fixed_income": 0.20,
}


def _classify(asset_class: str, sector: str | None) -> str:
    if asset_class == "etf" and (sector or "").lower() == "fixed_income":
        return "fixed_income"
    return asset_class


def _drift(current: dict[str, float]) -> list[RebalanceSuggestion]:
    total = sum(current.values()) or 1.0
    out: list[RebalanceSuggestion] = []
    for cls, tgt in TARGET.items():
        cw = current.get(cls, 0.0) / total
        d = round(cw - tgt, 4)
        action = "hold"
        if d <= -0.05:
            action = "add"
        elif d >= 0.05:
            action = "trim"
        out.append(RebalanceSuggestion(
            asset_class=cls, current_weight=cw, target_weight=tgt,
            drift=d, action=action,
        ))
    return out


@router.get("/suggestions", response_model=list[RebalanceSuggestion])
async def suggestions(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = CurrentUserDep,
) -> list[RebalanceSuggestion]:
    rows = await db.execute(
        select(Holding, Account, Security, Price.close)
        .join(Account, Account.id == Holding.account_id)
        .join(Security, Security.id == Holding.security_id)
        .join(Price, Price.security_id == Holding.security_id, isouter=True)
        .where(Account.user_id == user.id)
    )
    seen: set = set()
    weights: dict[str, float] = {}
    for h, _acc, sec, close in rows.all():
        if h.id in seen:
            continue
        seen.add(h.id)
        px = float(close) if close is not None else 0.0
        cls = _classify(sec.asset_class, sec.sector)
        weights[cls] = weights.get(cls, 0.0) + float(h.quantity) * px

    if not weights:
        # seed
        return [
            RebalanceSuggestion(asset_class="equity_us", current_weight=0.46,
                                target_weight=0.40, drift=0.06, action="trim"),
            RebalanceSuggestion(asset_class="equity_ca", current_weight=0.18,
                                target_weight=0.20, drift=-0.02, action="hold"),
            RebalanceSuggestion(asset_class="bonds", current_weight=0.08,
                                target_weight=0.20, drift=-0.12, action="add"),
            RebalanceSuggestion(asset_class="reit", current_weight=0.07,
                                target_weight=0.05, drift=0.02, action="hold"),
            RebalanceSuggestion(asset_class="cash", current_weight=0.21,
                                target_weight=0.15, drift=0.06, action="deploy"),
        ]
    return _drift(weights)


@router.get("/plan", response_model=RebalancePlan)
async def detailed_plan(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = CurrentUserDep,
) -> RebalancePlan:
    rows = await db.execute(
        select(Holding, Account, Security, Price.close)
        .join(Account, Account.id == Holding.account_id)
        .join(Security, Security.id == Holding.security_id)
        .join(Price, Price.security_id == Holding.security_id, isouter=True)
        .where(Account.user_id == user.id)
    )
    seen: set = set()
    holdings: list[HoldingForRebalance] = []
    weights: dict[str, float] = {}
    for h, acc, sec, close in rows.all():
        if h.id in seen:
            continue
        seen.add(h.id)
        px = Decimal(close) if close is not None else Decimal(0)
        mv = float(h.quantity * px)
        cls = _classify(sec.asset_class, sec.sector)
        holdings.append(HoldingForRebalance(
            account_id=str(acc.id),
            account_type=acc.account_type,
            symbol=sec.symbol,
            asset_class=cls,
            market_value_cad=mv,
            acb_total_cad=float(h.acb_total_cad),
            quantity=float(h.quantity),
        ))
        weights[cls] = weights.get(cls, 0.0) + mv

    if not holdings:
        return RebalancePlan(suggestions=await suggestions(db, user), actions=[])

    actions = plan(holdings, TARGET, available_cash_cad=0.0,
                   new_contribution_cad=2000.0)
    return RebalancePlan(
        suggestions=_drift(weights),
        actions=[
            ActionOut(
                account=a.account, action=a.action, symbol=a.symbol,
                amount_cad=a.amount_cad, reason=a.reason,
            )
            for a in actions
        ],
    )
