"""Adjusted cost base calculator.

Canadian average-cost-base method per holding, in CAD.
Buys add to ACB total + quantity. Sells reduce ACB proportionally and
realize a capital gain/loss against the running per-unit ACB.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class AcbLot:
    quantity: Decimal
    acb_total_cad: Decimal


@dataclass
class AcbResult:
    quantity: Decimal = Decimal(0)
    acb_total_cad: Decimal = Decimal(0)
    realized_gain_cad: Decimal = Decimal(0)
    history: list[dict[str, str]] = field(default_factory=list)

    @property
    def acb_per_unit(self) -> Decimal:
        if self.quantity == 0:
            return Decimal(0)
        return self.acb_total_cad / self.quantity


def apply_buy(state: AcbResult, quantity: Decimal, amount_cad: Decimal) -> AcbResult:
    state.quantity += quantity
    state.acb_total_cad += amount_cad
    state.history.append({"event": "buy", "qty": str(quantity), "amount_cad": str(amount_cad)})
    return state


def apply_sell(state: AcbResult, quantity: Decimal, proceeds_cad: Decimal) -> AcbResult:
    if state.quantity <= 0:
        raise ValueError("cannot sell from empty position")
    if quantity > state.quantity:
        raise ValueError("sell quantity exceeds holding")

    per_unit = state.acb_per_unit
    cost_basis_sold = per_unit * quantity
    realized = proceeds_cad - cost_basis_sold

    state.quantity -= quantity
    state.acb_total_cad -= cost_basis_sold
    state.realized_gain_cad += realized
    state.history.append(
        {
            "event": "sell",
            "qty": str(quantity),
            "proceeds_cad": str(proceeds_cad),
            "realized_gain_cad": str(realized),
        }
    )
    return state
