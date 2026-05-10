from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class RebalanceSuggestion(BaseModel):
    asset_class: str
    current_weight: float
    target_weight: float
    drift: float
    action: str


@router.get("/suggestions", response_model=list[RebalanceSuggestion])
async def suggestions() -> list[RebalanceSuggestion]:
    return [
        RebalanceSuggestion(
            asset_class="equity_us", current_weight=0.46, target_weight=0.40,
            drift=0.06, action="trim",
        ),
        RebalanceSuggestion(
            asset_class="equity_ca", current_weight=0.18, target_weight=0.20,
            drift=-0.02, action="hold",
        ),
        RebalanceSuggestion(
            asset_class="bonds", current_weight=0.08, target_weight=0.20,
            drift=-0.12, action="add",
        ),
        RebalanceSuggestion(
            asset_class="reit", current_weight=0.07, target_weight=0.05,
            drift=0.02, action="hold",
        ),
        RebalanceSuggestion(
            asset_class="cash", current_weight=0.21, target_weight=0.15,
            drift=0.06, action="deploy",
        ),
    ]
