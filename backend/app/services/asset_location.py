"""Asset location optimizer.

Canadian framing:
  - US-listed equities → RRSP (no 15% withholding under tax treaty)
  - Canadian dividend equities → non-registered (dividend tax credit)
  - High-growth equities → TFSA (long-horizon tax-free compounding)
  - Bonds + REITs → tax-sheltered (interest distributions are taxed as
    ordinary income)
  - International equities → TFSA or non-reg (TFSA loses treaty benefit
    for some jurisdictions; we flag, not prescribe)

Output is a list of recommendations describing where each holding
*ideally* lives, plus a reason. We never tell the user to sell. The
expected human action is to gradually direct future contributions.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HoldingPlacement:
    symbol: str
    asset_class: str
    sector: str | None
    region: str | None
    is_dividend_payer: bool
    current_account_type: str


@dataclass
class PlacementSuggestion:
    symbol: str
    current_account_type: str
    recommended_account_type: str
    reason: str


def _ideal(h: HoldingPlacement) -> tuple[str, str]:
    """Return (account_type, reason)."""
    cls = h.asset_class.lower()
    region = (h.region or "").lower()

    if cls in {"bond", "fixed_income"} or h.asset_class == "etf" and (h.sector or "").lower() == "fixed_income":
        return "rrsp", "Bond interest is taxed as ordinary income. Sheltering it preserves the most after-tax yield."
    if cls == "reit":
        return "tfsa", "REIT distributions are taxed as ordinary income at the trust level. Sheltering them avoids that drag."
    if region == "us" and cls in {"equity", "etf"}:
        if h.is_dividend_payer:
            return "rrsp", "US dividends in an RRSP avoid the 15% withholding under the Canada–US tax treaty."
        return "rrsp", "US-listed equities are generally most tax-efficient inside an RRSP."
    if region == "ca" and cls == "equity" and h.is_dividend_payer:
        return "non_reg", "Canadian dividends qualify for the dividend tax credit, which has more value outside registered accounts."
    if cls == "equity" and not h.is_dividend_payer:
        return "tfsa", "High-growth, non-dividend-paying equities benefit most from tax-free compounding inside a TFSA."
    return h.current_account_type, "Already in a reasonable account for its profile."


def recommend_placement(holdings: list[HoldingPlacement]) -> list[PlacementSuggestion]:
    out: list[PlacementSuggestion] = []
    for h in holdings:
        rec, reason = _ideal(h)
        if rec == h.current_account_type:
            continue
        out.append(PlacementSuggestion(
            symbol=h.symbol,
            current_account_type=h.current_account_type,
            recommended_account_type=rec,
            reason=reason,
        ))
    return out
