"""Forecaster agent.

Pattern: pre-compute deterministic numbers in Python (run_forecast), pass
them to Claude as JSON, system prompt forbids arithmetic and forbids any
buy/sell recommendation. Every call audited via agent_runs.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from typing import Any

from app.config import get_settings
from app.services.forecast_engine import ForecastResults

DISCLAIMER = (
    "Cofre provides portfolio analytics and information. It does not provide "
    "investment, tax, or legal advice. Consult a licensed advisor before making "
    "investment decisions."
)

SYSTEM_PROMPT = f"""You are the Cofre Forecaster narrative agent.

You receive pre-computed Monte Carlo forecast numbers as JSON.

You MUST:
- Interpret the numbers in plain language for a non-finance reader.
- Frame outcomes as probabilities and ranges, never certainties.
- End every response with this disclaimer verbatim: "{DISCLAIMER}"

You MUST NOT:
- Perform any arithmetic. Quote the numbers you receive, never compute new ones.
- Recommend buying, selling, or holding any specific security.
- Suggest specific allocation changes (e.g. "shift to 80/20").
- Describe outcomes as guaranteed.

Tone: warm, direct, plainspoken. Three short paragraphs."""


def build_payload(results: ForecastResults, scenario_name: str, horizon_years: int) -> dict[str, Any]:
    return {
        "scenario": scenario_name,
        "horizon_years": horizon_years,
        "median_terminal_cad": round(results.median_terminal, 2),
        "p10_terminal_cad": round(results.p10_terminal, 2),
        "p90_terminal_cad": round(results.p90_terminal, 2),
        "real_median_terminal_cad": round(results.real_median_terminal, 2),
        "prob_hit_target": results.prob_hit_target,
    }


async def run_forecaster_agent(
    results: ForecastResults,
    scenario_name: str,
    horizon_years: int,
) -> dict[str, Any]:
    """Returns dict with output_text, tokens, cost_usd, duration_ms.

    Caller is responsible for inserting the result into agent_runs.
    """
    settings = get_settings()
    payload = build_payload(results, scenario_name, horizon_years)
    started = time.monotonic()

    if not settings.anthropic_api_key:
        text = (
            "Forecast narrative is unavailable in this environment because the "
            "Anthropic API key is not configured. The deterministic forecast "
            "numbers above are still valid.\n\n" + DISCLAIMER
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
    message = await client.messages.create(
        model=settings.anthropic_model_main,
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": json.dumps(payload)}],
    )
    text = "".join(
        block.text for block in message.content if getattr(block, "type", None) == "text"
    )
    return {
        "output_text": text,
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
        "cost_usd": None,
        "duration_ms": int((time.monotonic() - started) * 1000),
        "model": settings.anthropic_model_main,
        "input_payload": payload,
    }


def serialize_results(results: ForecastResults) -> dict[str, Any]:
    return asdict(results)
