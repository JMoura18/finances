from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class AgentRunOut(BaseModel):
    id: str
    agent_name: str
    model: str
    duration_ms: int | None
    cost_usd: float | None
    created_at: datetime


@router.get("/runs", response_model=list[AgentRunOut])
async def list_runs() -> list[AgentRunOut]:
    return [
        AgentRunOut(
            id="ar-1",
            agent_name="forecaster",
            model="claude-opus-4-7",
            duration_ms=2840,
            cost_usd=0.012,
            created_at=datetime(2026, 5, 9, 21, 14),
        ),
        AgentRunOut(
            id="ar-2",
            agent_name="risk_analyst",
            model="claude-opus-4-7",
            duration_ms=3120,
            cost_usd=0.014,
            created_at=datetime(2026, 5, 8, 17, 2),
        ),
    ]
