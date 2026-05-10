"""CSV transaction import.

Expected columns (case-insensitive, order-independent):
  occurred_at, txn_type, symbol, quantity, price, amount, currency, fx_rate, notes

Every row is validated. Rows with errors are returned alongside successes
so the UI can show a per-row outcome.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation

ALLOWED_TYPES = {
    "buy", "sell", "dividend", "interest", "contribution",
    "withdrawal", "fee", "split", "transfer_in", "transfer_out",
}


@dataclass
class ParsedTxn:
    occurred_at: datetime
    txn_type: str
    symbol: str | None
    quantity: Decimal | None
    price: Decimal | None
    amount_native: Decimal
    currency: str
    fx_rate: Decimal
    amount_cad: Decimal
    notes: str | None


@dataclass
class ParseResult:
    parsed: list[ParsedTxn] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)


def _to_decimal(s: str | None) -> Decimal | None:
    if s is None or str(s).strip() == "":
        return None
    try:
        return Decimal(str(s).replace(",", "").strip())
    except InvalidOperation as e:
        raise ValueError(f"invalid number {s!r}") from e


def _to_dt(s: str) -> datetime:
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"unrecognized date format {s!r}")


def parse_csv(content: str) -> ParseResult:
    result = ParseResult()
    reader = csv.DictReader(io.StringIO(content))

    for row_num, raw in enumerate(reader, start=2):
        try:
            row = {(k or "").lower().strip(): (v or "").strip() for k, v in raw.items()}
            txn_type = row.get("txn_type", "").lower()
            if txn_type not in ALLOWED_TYPES:
                raise ValueError(f"invalid txn_type {txn_type!r}")

            quantity = _to_decimal(row.get("quantity"))
            price = _to_decimal(row.get("price"))
            amount_native = _to_decimal(row.get("amount"))
            if amount_native is None:
                raise ValueError("amount is required")

            currency = (row.get("currency") or "CAD").upper()
            fx_rate = _to_decimal(row.get("fx_rate")) or Decimal("1")
            amount_cad = amount_native * fx_rate

            result.parsed.append(
                ParsedTxn(
                    occurred_at=_to_dt(row["occurred_at"]),
                    txn_type=txn_type,
                    symbol=row.get("symbol") or None,
                    quantity=quantity,
                    price=price,
                    amount_native=amount_native,
                    currency=currency,
                    fx_rate=fx_rate,
                    amount_cad=amount_cad,
                    notes=row.get("notes") or None,
                )
            )
        except Exception as e:
            result.errors.append({"row": str(row_num), "error": str(e)})

    return result
