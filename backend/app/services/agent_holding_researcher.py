"""Holding Researcher agent.

Receives a JSON dossier (symbol, name, sector, fundamentals, top news
headlines, earnings dates) and produces a balanced narrative.

Same hard rules: no arithmetic, no buy/sell recommendations, disclaimer
at the end, audited via agent_runs.
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

SYSTEM_PROMPT = f"""You are the Cofre Holding Researcher narrative agent.

You receive a JSON dossier about a single security: symbol, name, sector,
fundamentals (e.g. P/E, dividend yield, market cap), recent news
headlines with relevance scores, and the next earnings date if known.

You MUST:
- Synthesize what an informed observer would notice. What's the story?
- Mention both the bullish read and the bearish read where applicable.
- Reference the news headlines you were given by their text.
- End every response with this disclaimer verbatim: "{DISCLAIMER}"

You MUST NOT:
- Perform arithmetic. Cite the fundamentals you receive without computing
  derived ratios.
- Recommend buying, selling, or holding the security. Phrase observations
  neutrally.
- Speculate beyond what's in the dossier. If a number is missing, say so.

Tone: warm, direct, plainspoken. Three short paragraphs."""


async def run_holding_researcher(dossier: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    started = time.monotonic()

    if not settings.anthropic_api_key:
        text = (
            f"Research narrative for {dossier.get('symbol')} requires an "
            f"Anthropic API key. The fundamentals and news shown above are "
            f"the deterministic source.\n\n" + DISCLAIMER
        )
        return {
            "output_text": text,
            "input_tokens": None,
            "output_tokens": None,
            "cost_usd": None,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "model": settings.anthropic_model_main,
            "input_payload": dossier,
        }

    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    msg = await client.messages.create(
        model=settings.anthropic_model_main,
        max_tokens=700,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": json.dumps(dossier)}],
    )
    text = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
    return {
        "output_text": text,
        "input_tokens": msg.usage.input_tokens,
        "output_tokens": msg.usage.output_tokens,
        "cost_usd": None,
        "duration_ms": int((time.monotonic() - started) * 1000),
        "model": settings.anthropic_model_main,
        "input_payload": dossier,
    }
