from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HoldingOut(BaseModel):
    id: str
    account_id: str
    symbol: str
    name: str
    asset_class: str
    sector: str | None
    region: str | None
    quantity: float
    last_price_cad: float
    market_value_cad: float
    acb_total_cad: float
    unrealized_pnl_cad: float
    weight: float


@router.get("", response_model=list[HoldingOut])
async def list_holdings() -> list[HoldingOut]:
    seed = [
        ("h-vfv", "acc-tfsa", "VFV.TO", "Vanguard S&P 500", "etf", "tech", "us", 180, 132.40, 23832.00, 18900.00),
        ("h-veqt", "acc-rrsp", "VEQT.TO", "Vanguard All-Equity ETF", "etf", "diversified", "global", 420, 38.10, 16002.00, 14700.00),
        ("h-xeqt", "acc-tfsa", "XEQT.TO", "iShares All-Equity ETF", "etf", "diversified", "global", 600, 32.85, 19710.00, 17800.00),
        ("h-shop", "acc-non-reg", "SHOP.TO", "Shopify", "equity", "tech", "ca", 90, 110.20, 9918.00, 7200.00),
        ("h-msft", "acc-rrsp", "MSFT", "Microsoft", "equity", "tech", "us", 40, 510.30, 27776.32, 21200.00),
        ("h-cnq", "acc-non-reg", "CNQ.TO", "Canadian Natural Resources", "equity", "energy", "ca", 200, 51.20, 10240.00, 9100.00),
        ("h-rein", "acc-tfsa", "REI.UN.TO", "RioCan REIT", "reit", "real_estate", "ca", 500, 19.40, 9700.00, 11200.00),
        ("h-bnd", "acc-rrsp", "ZAG.TO", "BMO Aggregate Bond ETF", "etf", "fixed_income", "ca", 800, 14.10, 11280.00, 12100.00),
    ]
    total = sum(row[9] for row in seed)
    out: list[HoldingOut] = []
    for row in seed:
        (id_, acc, sym, name, cls, sector, region, qty, px, mv, acb) = row
        out.append(
            HoldingOut(
                id=id_,
                account_id=acc,
                symbol=sym,
                name=name,
                asset_class=cls,
                sector=sector,
                region=region,
                quantity=float(qty),
                last_price_cad=float(px),
                market_value_cad=float(mv),
                acb_total_cad=float(acb),
                unrealized_pnl_cad=float(mv - acb),
                weight=float(mv / total) if total else 0.0,
            )
        )
    return out
