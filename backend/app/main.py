from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import (
    accounts,
    agents,
    alerts,
    calibration,
    forecast,
    holdings,
    rebalance,
    risk,
    snaptrade,
    tax,
    transactions,
    users,
)

DISCLAIMER = (
    "Cofre provides portfolio analytics and information. It does not provide "
    "investment, tax, or legal advice. Consult a licensed advisor before making "
    "investment decisions."
)

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    if settings.environment == "dev":
        try:
            from scripts.seed_dev import seed
            await seed()
        except Exception as e:  # noqa: BLE001
            log.warning("dev seed skipped: %s", e)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Cofre API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"name": "Cofre API", "version": "0.1.0", "disclaimer": DISCLAIMER}

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(users.router, prefix="/api/users", tags=["users"])
    app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])
    app.include_router(holdings.router, prefix="/api/holdings", tags=["holdings"])
    app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
    app.include_router(forecast.router, prefix="/api/forecast", tags=["forecast"])
    app.include_router(risk.router, prefix="/api/risk", tags=["risk"])
    app.include_router(tax.router, prefix="/api/tax", tags=["tax"])
    app.include_router(rebalance.router, prefix="/api/rebalance", tags=["rebalance"])
    app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
    app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
    app.include_router(snaptrade.router, prefix="/api/snaptrade", tags=["snaptrade"])
    app.include_router(calibration.router, prefix="/api/calibration", tags=["calibration"])

    return app


app = create_app()
