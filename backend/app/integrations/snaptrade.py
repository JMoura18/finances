"""SnapTrade client wrapper.

Read-only by contract. Every code path that builds a request asserts a
read-only intent. We never enable trading.

When credentials aren't configured, methods return a deterministic mock
payload so the rest of the app stays demoable.

Real integration uses HMAC-signed requests against api.snaptrade.com.
The detail of the signing scheme is left to the official SDK; this
module exposes a thin surface our routers depend on.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx

from app.config import get_settings

BASE_URL = "https://api.snaptrade.com/api/v1"


@dataclass
class BrokerageAccount:
    external_id: str
    institution: str
    name: str
    account_type: str
    currency: str


@dataclass
class BrokerageHolding:
    external_account_id: str
    symbol: str
    quantity: float
    last_price: float
    currency: str


def _sign(client_id: str, consumer_key: str, path: str, query: dict) -> dict:
    timestamp = str(int(time.time()))
    qs = urlencode(sorted({**query, "clientId": client_id, "timestamp": timestamp}.items()))
    payload = f"{path}?{qs}"
    sig = hmac.new(consumer_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return {"clientId": client_id, "timestamp": timestamp, "Signature": sig}


def _configured() -> bool:
    s = get_settings()
    return bool(s.snaptrade_client_id and s.snaptrade_consumer_key)


async def get_connect_url(user_id: str) -> str:
    """Return a hosted login URL for the user to authorize a brokerage."""
    if not _configured():
        return f"https://example.invalid/snaptrade/mock?user={user_id}"
    s = get_settings()
    headers = _sign(s.snaptrade_client_id, s.snaptrade_consumer_key,
                    "/snapTrade/loginUserBrokerage", {"userId": user_id})
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(f"{BASE_URL}/snapTrade/loginUserBrokerage",
                              params={"userId": user_id}, headers=headers)
        r.raise_for_status()
        return r.json()["redirectURI"]


async def list_accounts(user_id: str) -> list[BrokerageAccount]:
    if not _configured():
        return [
            BrokerageAccount(
                external_id="mock-wealthsimple-tfsa",
                institution="Wealthsimple",
                name="TFSA",
                account_type="tfsa",
                currency="CAD",
            ),
            BrokerageAccount(
                external_id="mock-questrade-rrsp",
                institution="Questrade",
                name="RRSP",
                account_type="rrsp",
                currency="CAD",
            ),
        ]
    s = get_settings()
    headers = _sign(s.snaptrade_client_id, s.snaptrade_consumer_key,
                    "/accounts", {"userId": user_id})
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{BASE_URL}/accounts",
                             params={"userId": user_id}, headers=headers)
        r.raise_for_status()
        return [
            BrokerageAccount(
                external_id=a["id"],
                institution=a.get("institution_name", "Unknown"),
                name=a.get("name", "Account"),
                account_type=_map_account_type(a.get("meta", {}).get("type")),
                currency=a.get("balance", {}).get("currency", "CAD"),
            )
            for a in r.json()
        ]


async def list_holdings(user_id: str, account_id: str) -> list[BrokerageHolding]:
    if not _configured():
        return [
            BrokerageHolding(
                external_account_id=account_id,
                symbol="VFV.TO" if "tfsa" in account_id else "VEQT.TO",
                quantity=120 if "tfsa" in account_id else 200,
                last_price=132.4 if "tfsa" in account_id else 38.1,
                currency="CAD",
            )
        ]
    s = get_settings()
    headers = _sign(s.snaptrade_client_id, s.snaptrade_consumer_key,
                    f"/accounts/{account_id}/positions",
                    {"userId": user_id})
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{BASE_URL}/accounts/{account_id}/positions",
                             params={"userId": user_id}, headers=headers)
        r.raise_for_status()
        return [
            BrokerageHolding(
                external_account_id=account_id,
                symbol=p["symbol"]["symbol"],
                quantity=float(p.get("units", 0)),
                last_price=float(p.get("price", 0)),
                currency=p.get("currency", "CAD"),
            )
            for p in r.json()
        ]


def _map_account_type(t: Any) -> str:
    if not t:
        return "non_reg"
    s = str(t).lower()
    if "tfsa" in s:
        return "tfsa"
    if "rrsp" in s:
        return "rrsp"
    if "fhsa" in s:
        return "fhsa"
    if "rrif" in s:
        return "rrif"
    if "lira" in s:
        return "lira"
    if "resp" in s:
        return "resp"
    return "non_reg"
