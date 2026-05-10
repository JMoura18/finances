"""News relevance + sentiment.

Two pieces:

1. _Relevance_ — keyword-overlap scoring against the security's symbol,
   name, and sector. Cheap and explainable; pluggable for an embedding
   model later.

2. _Sentiment_ — VADER-style lexicon polarity, again deterministic. We
   intentionally don't ship sentiment as fact — it's an aid for triage.

Both produce floats in [0, 1] (relevance) and [-1, 1] (sentiment).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

POSITIVE_TERMS = {
    "beats", "beat", "upgrade", "growth", "record", "strong", "surge",
    "rally", "outperform", "raises", "raise", "wins", "approved", "buy",
    "expands", "expansion", "launches", "exceeds",
}
NEGATIVE_TERMS = {
    "misses", "miss", "downgrade", "loss", "weak", "drops", "plunge",
    "underperform", "cuts", "cut", "lawsuit", "investigation", "recall",
    "fired", "delays", "delay", "warns", "warning",
}


def _tokens(s: str) -> list[str]:
    return [t.lower().strip(".,!?;:'\"") for t in s.split()]


@dataclass
class RankedHeadline:
    headline: str
    url: str
    source: str
    relevance: float
    sentiment: float


def rank_headlines(
    headlines: Iterable[dict],
    *,
    symbol: str,
    name: str | None,
    sector: str | None,
) -> list[RankedHeadline]:
    target_terms = {symbol.lower()}
    if name:
        target_terms.update(_tokens(name))
    if sector:
        target_terms.update(_tokens(sector))
    target_terms = {t for t in target_terms if len(t) >= 3}

    out: list[RankedHeadline] = []
    for h in headlines:
        text = h.get("headline", "") or ""
        toks = set(_tokens(text))
        rel = len(toks & target_terms) / max(len(target_terms), 1)

        pos = sum(1 for t in toks if t in POSITIVE_TERMS)
        neg = sum(1 for t in toks if t in NEGATIVE_TERMS)
        total = pos + neg
        sent = ((pos - neg) / total) if total else 0.0

        out.append(RankedHeadline(
            headline=text,
            url=h.get("url", ""),
            source=h.get("source", ""),
            relevance=round(rel, 3),
            sentiment=round(sent, 3),
        ))
    out.sort(key=lambda r: r.relevance, reverse=True)
    return out
