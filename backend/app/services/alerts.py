"""Alert pipeline.

Deterministic rule set. Each rule produces zero or more Alert candidates.
Pipeline is idempotent: re-running won't insert duplicates within a 24h
window for the same (user, category, key) tuple.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AlertCandidate:
    severity: str
    title: str
    body: str
    category: str
    key: str  # de-dupe key


def evaluate_alerts(
    composite_score: float,
    regime: str,
    concentration: dict,
    stress_results: dict[str, float],
    drift_by_class: dict[str, float] | None = None,
) -> list[AlertCandidate]:
    out: list[AlertCandidate] = []

    if composite_score >= 75:
        out.append(AlertCandidate(
            severity="critical",
            title="Risk score elevated",
            body=f"Composite risk is {composite_score:.0f}/100. Regime: {regime}.",
            category="risk_score",
            key="risk_score:high",
        ))
    elif composite_score >= 55:
        out.append(AlertCandidate(
            severity="warn",
            title="Risk score notable",
            body=f"Composite risk is {composite_score:.0f}/100. Worth a look.",
            category="risk_score",
            key="risk_score:notable",
        ))

    hhi = concentration.get("hhi", 0.0)
    if hhi >= 0.30:
        out.append(AlertCandidate(
            severity="warn",
            title="Concentration is high",
            body=f"Portfolio HHI is {hhi:.2f}. A few names dominate.",
            category="concentration",
            key="concentration:hhi_high",
        ))

    top = concentration.get("top", [])
    if top and top[0].get("weight", 0) >= 0.20:
        sym = top[0]["symbol"]
        w = top[0]["weight"]
        out.append(AlertCandidate(
            severity="warn",
            title=f"{sym} is {w:.0%} of portfolio",
            body=f"Single-name concentration at {w:.0%}.",
            category="concentration",
            key=f"concentration:single_{sym}",
        ))

    by_sector = concentration.get("by_sector", {})
    for sector, w in by_sector.items():
        if w >= 0.40:
            out.append(AlertCandidate(
                severity="warn",
                title=f"{sector.replace('_', ' ').title()} concentration",
                body=f"{w:.0%} of portfolio is in one sector.",
                category="concentration",
                key=f"concentration:sector_{sector}",
            ))

    worst_stress = min(stress_results.values(), default=0.0)
    if worst_stress <= -0.40:
        out.append(AlertCandidate(
            severity="critical",
            title="Stress drawdown severe",
            body=f"Worst-case modeled drawdown is {worst_stress:.0%}.",
            category="stress",
            key="stress:severe",
        ))
    elif worst_stress <= -0.25:
        out.append(AlertCandidate(
            severity="warn",
            title="Stress drawdown elevated",
            body=f"Worst-case modeled drawdown is {worst_stress:.0%}.",
            category="stress",
            key="stress:elevated",
        ))

    if regime in {"elevated", "crisis"}:
        out.append(AlertCandidate(
            severity="warn" if regime == "elevated" else "critical",
            title=f"Market regime: {regime}",
            body=f"Regime classifier flagged {regime} conditions.",
            category="regime",
            key=f"regime:{regime}",
        ))

    if drift_by_class:
        for cls, drift in drift_by_class.items():
            if abs(drift) >= 0.10:
                out.append(AlertCandidate(
                    severity="info",
                    title=f"Allocation drift: {cls}",
                    body=f"{cls} is {drift:+.0%} from target.",
                    category="rebalance",
                    key=f"rebalance:{cls}",
                ))

    return out
