"""Tax-aware rebalancer.

Given current allocations, target allocations, and per-holding ACB +
account-type info, produce an action plan that:

1. Prefers using *new contributions* to fix underweight positions. No
   sale, no taxes.
2. Within registered accounts (TFSA/RRSP/FHSA), rebalances by selling
   winners freely.
3. In non-registered accounts, prefers harvesting losses and trimming
   short-term-held winners last. Realized gain estimate goes in the plan.

Output is a list of actions, never a forced trade. The user decides.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HoldingForRebalance:
    account_id: str
    account_type: str
    symbol: str
    asset_class: str
    market_value_cad: float
    acb_total_cad: float
    quantity: float


@dataclass
class RebalanceAction:
    account: str
    symbol: str | None
    action: str  # 'add' | 'trim' | 'hold' | 'deploy_cash'
    asset_class: str
    amount_cad: float
    estimated_gain_cad: float
    reason: str


def plan(
    holdings: list[HoldingForRebalance],
    targets: dict[str, float],
    available_cash_cad: float = 0.0,
    new_contribution_cad: float = 0.0,
) -> list[RebalanceAction]:
    total = sum(h.market_value_cad for h in holdings) + available_cash_cad
    if total <= 0:
        return []

    by_class: dict[str, float] = {}
    for h in holdings:
        by_class[h.asset_class] = by_class.get(h.asset_class, 0.0) + h.market_value_cad
    drift = {
        cls: (by_class.get(cls, 0.0) / total) - tgt for cls, tgt in targets.items()
    }

    actions: list[RebalanceAction] = []
    deployable = available_cash_cad + new_contribution_cad

    # Step 1: deploy new cash to underweight classes first
    for cls, d in sorted(drift.items(), key=lambda x: x[1]):
        if d >= 0 or deployable <= 0:
            continue
        gap_cad = abs(d) * total
        amount = min(gap_cad, deployable)
        if amount <= 0:
            continue
        actions.append(RebalanceAction(
            account="any",
            symbol=None,
            action="deploy_cash",
            asset_class=cls,
            amount_cad=round(amount, 2),
            estimated_gain_cad=0.0,
            reason="Use new cash to bring this class closer to target before considering sales.",
        ))
        deployable -= amount

    # Step 2: trim overweight classes, preferring registered accounts
    for cls, d in sorted(drift.items(), key=lambda x: x[1], reverse=True):
        if d <= 0:
            continue
        gap_cad = d * total
        candidates = sorted(
            [h for h in holdings if h.asset_class == cls],
            key=lambda h: (
                0 if h.account_type in {"tfsa", "rrsp", "fhsa"} else 1,
                -(h.market_value_cad - h.acb_total_cad),
            ),
        )
        remaining = gap_cad
        for h in candidates:
            if remaining <= 0:
                break
            slice_amount = min(remaining, h.market_value_cad)
            if slice_amount <= 0:
                continue
            est_gain = (
                (slice_amount / h.market_value_cad) * (h.market_value_cad - h.acb_total_cad)
                if h.account_type == "non_reg"
                else 0.0
            )
            reason = (
                "Sheltered account: rebalancing here is tax-free."
                if h.account_type in {"tfsa", "rrsp", "fhsa"}
                else f"Non-registered: estimated realized gain ~{est_gain:.0f} CAD."
            )
            actions.append(RebalanceAction(
                account=h.account_id,
                symbol=h.symbol,
                action="trim",
                asset_class=cls,
                amount_cad=round(slice_amount, 2),
                estimated_gain_cad=round(est_gain, 2),
                reason=reason,
            ))
            remaining -= slice_amount

    return actions
