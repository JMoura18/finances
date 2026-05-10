"""Risk Analyst narrative agent.

Receives a deterministic risk snapshot. Interprets concentration, regime,
and stress results in plain language. Same audit + disclaimer rules as
the Forecaster.
"""

from __future__ import annotations

import json
import time
from typing import Any

from app.config import get_settings

DISCLAIMER = (
    "Cofre provides portfolio analytics and information. It does not provide "
    "investment, tax, or legal advice. Consult a licensed advisor before making "
    "investment decisions."
)

SYSTEM_PROMPT = f"""You are the Cofre Risk Analyst narrative agent.

You receive pre-computed risk numbers as JSON: composite score (0-100),
regime label, HHI concentration, sector breakdown, and historical stress
drawdowns.

You MUST:
- Interpret the numbers in plain language for a non-finance reader.
- Highlight the top concentration risks and worst stress outcome.
- End every response with this disclaimer verbatim: "{DISCLAIMER}"

You MUST NOT:
- Perform any arithmetic. Quote the numbers you receive.
- Recommend buying, selling, or holding any specific security.
- Recommend specific allocation changes.
- Describe outcomes as guaranteed.

Tone: warm, direct, plainspoken. Two short paragraphs."""


async def run_risk_analyst_agent(
    score: float,
    regime: str,
    concentration: dict[str, Any],
    stress_results: dict[str, float],
) -> dict[str, Any]:
    settings = get_settings()
    payload = {
        "composite_score": score,
        "regime": regime,
        "hhi": concentration.get("hhi"),
        "top_holdings": concentration.get("top", [])[:3],
        "by_sector": concentration.get("by_sector", {}),
        "stress_results_pct": {
            k: round(v * 100, 1) for k, v in stress_results.items()
        },
    }
    started = time.monotonic()

    if not settings.anthropic_api_key:
        text = (
            f"Your composite risk score is {score:.0f}/100 in a "
            f"{regime} regime. Concentration metrics and stress results are "
            f"shown above. The narrative agent requires an Anthropic API key.\n\n"
            + DISCLAIMER
        )
        return {
            "output_text": text,
            "input_tokens": None,
            "output_tokens": None,
            "cost_usd": None,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "model": settings.anthropic_model_main,
            "input_payload": payload,
        }

    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    msg = await client.messages.create(
        model=settings.anthropic_model_main,
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": json.dumps(payload)}],
    )
    text = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
    return {
        "output_text": text,
        "input_tokens": msg.usage.input_tokens,
        "output_tokens": msg.usage.output_tokens,
        "cost_usd": None,
        "duration_ms": int((time.monotonic() - started) * 1000),
        "model": settings.anthropic_model_main,
        "input_payload": payload,
    }
