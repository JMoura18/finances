"""Portfolio aggregation.

Holdings derive from transactions. ACB is recomputed from scratch using
the average-cost method. This is the source of truth — never mutate
holdings directly.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from app.services.acb import AcbResult, apply_buy, apply_sell


@dataclass
class TxnInput:
    account_id: uuid.UUID
    security_id: uuid.UUID | None
    txn_type: str
    quantity: Decimal | None
    amount_cad: Decimal
    occurred_at_iso: str  # for stable sort


@dataclass
class DerivedHolding:
    account_id: uuid.UUID
    security_id: uuid.UUID
    quantity: Decimal
    acb_total_cad: Decimal
    realized_gain_cad: Decimal


def derive_holdings(transactions: list[TxnInput]) -> list[DerivedHolding]:
    """Group by (account, security), sort by time, apply buys/sells.

    Splits scale quantity proportionally; dividends/contributions/fees do not
    affect quantity or ACB.
    """
    grouped: dict[tuple[uuid.UUID, uuid.UUID], list[TxnInput]] = defaultdict(list)
    for t in transactions:
        if t.security_id is None:
            continue
        grouped[(t.account_id, t.security_id)].append(t)

    out: list[DerivedHolding] = []
    for (account_id, security_id), txns in grouped.items():
        txns.sort(key=lambda x: x.occurred_at_iso)
        state = AcbResult()
        for t in txns:
            if t.txn_type == "buy" and t.quantity is not None:
                apply_buy(state, t.quantity, t.amount_cad)
            elif t.txn_type == "sell" and t.quantity is not None:
                if state.quantity > 0:
                    qty = min(t.quantity, state.quantity)
                    apply_sell(state, qty, t.amount_cad)
            elif t.txn_type == "split" and t.quantity is not None:
                # quantity stores the split ratio (e.g. 2 for 2-for-1)
                state.quantity *= t.quantity
        if state.quantity > 0:
            out.append(
                DerivedHolding(
                    account_id=account_id,
                    security_id=security_id,
                    quantity=state.quantity,
                    acb_total_cad=state.acb_total_cad,
                    realized_gain_cad=state.realized_gain_cad,
                )
            )
    return out


@dataclass
class PortfolioTotals:
    market_value_cad: Decimal
    book_value_cad: Decimal
    unrealized_pnl_cad: Decimal


def value_portfolio(
    holdings: list[DerivedHolding],
    last_price_cad: dict[uuid.UUID, Decimal],
) -> PortfolioTotals:
    market = Decimal(0)
    book = Decimal(0)
    for h in holdings:
        px = last_price_cad.get(h.security_id, Decimal(0))
        market += h.quantity * px
        book += h.acb_total_cad
    return PortfolioTotals(
        market_value_cad=market,
        book_value_cad=book,
        unrealized_pnl_cad=market - book,
    )
