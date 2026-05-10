"""Reconciliation between manual entries and brokerage sync.

Sync is read-only and authoritative for *quantities and prices*. Manual
entries remain authoritative for *categorization and notes*.

When sync conflicts:
  - quantity differs → record a snapshot transaction with txn_type='transfer_in'
    or 'transfer_out' to bridge the difference, source='snaptrade'
  - new symbols seen in sync → create the security and a transfer_in
  - never delete manual transactions

This keeps `transactions` as the source of truth.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.snaptrade import BrokerageHolding, list_accounts, list_holdings
from app.models import Account, Holding, Security, Transaction
from app.services.portfolio import TxnInput, derive_holdings


@dataclass
class ReconciliationResult:
    accounts_synced: int = 0
    holdings_seen: int = 0
    transfers_created: int = 0
    new_securities: int = 0


async def _resolve_security(db: AsyncSession, symbol: str, currency: str) -> Security:
    rows = await db.execute(select(Security).where(Security.symbol == symbol.upper()))
    sec = rows.scalars().first()
    if sec:
        return sec
    sec = Security(symbol=symbol.upper(), exchange="UNKNOWN", asset_class="equity",
                   currency=currency, name=symbol.upper())
    db.add(sec)
    await db.flush()
    return sec


async def _account_for_external(
    db: AsyncSession, user_id: uuid.UUID, ext_id: str,
    name: str, kind: str, institution: str, currency: str,
) -> Account:
    rows = await db.execute(
        select(Account).where(Account.snaptrade_account_id == ext_id)
    )
    acc = rows.scalars().first()
    if acc:
        acc.is_synced = True
        return acc
    acc = Account(
        user_id=user_id, name=name, account_type=kind,
        currency=currency, institution=institution,
        snaptrade_account_id=ext_id, is_synced=True,
    )
    db.add(acc)
    await db.flush()
    return acc


async def reconcile_user(db: AsyncSession, user_id: uuid.UUID, user_external_id: str) -> ReconciliationResult:
    result = ReconciliationResult()

    accounts = await list_accounts(user_external_id)
    for ext_acc in accounts:
        acc = await _account_for_external(
            db, user_id, ext_acc.external_id, ext_acc.name,
            ext_acc.account_type, ext_acc.institution, ext_acc.currency,
        )
        result.accounts_synced += 1

        sync_holdings = await list_holdings(user_external_id, ext_acc.external_id)

        # Compute current holdings from manual transactions
        rows = await db.execute(
            select(Transaction).where(Transaction.account_id == acc.id)
        )
        txns = rows.scalars().all()
        derived = {
            h.security_id: h
            for h in derive_holdings([
                TxnInput(
                    account_id=t.account_id,
                    security_id=t.security_id,
                    txn_type=t.txn_type,
                    quantity=t.quantity,
                    amount_cad=t.amount_cad,
                    occurred_at_iso=t.occurred_at.isoformat(),
                )
                for t in txns
            ])
        }

        seen_symbols: set[str] = set()
        for sh in sync_holdings:
            seen_symbols.add(sh.symbol.upper())
            sec_before_count = (await db.execute(
                select(Security).where(Security.symbol == sh.symbol.upper())
            )).scalars().first()
            sec = await _resolve_security(db, sh.symbol, sh.currency)
            if sec_before_count is None:
                result.new_securities += 1
            result.holdings_seen += 1

            book_qty = derived.get(sec.id).quantity if sec.id in derived else Decimal(0)
            sync_qty = Decimal(str(sh.quantity))
            diff = sync_qty - book_qty
            if diff == 0:
                continue

            kind = "transfer_in" if diff > 0 else "transfer_out"
            qty = abs(diff)
            amount_cad = qty * Decimal(str(sh.last_price))
            db.add(Transaction(
                account_id=acc.id,
                security_id=sec.id,
                txn_type=kind,
                quantity=qty,
                price=Decimal(str(sh.last_price)),
                amount_native=amount_cad,
                currency=sh.currency,
                fx_rate=Decimal("1"),
                amount_cad=amount_cad,
                occurred_at=datetime.now(timezone.utc),
                notes="reconciled from SnapTrade",
                source="snaptrade",
            ))
            result.transfers_created += 1

        # Recompute holdings from updated transactions
        rows = await db.execute(
            select(Transaction).where(Transaction.account_id == acc.id)
        )
        txns = rows.scalars().all()
        new_derived = derive_holdings([
            TxnInput(
                account_id=t.account_id,
                security_id=t.security_id,
                txn_type=t.txn_type,
                quantity=t.quantity,
                amount_cad=t.amount_cad,
                occurred_at_iso=t.occurred_at.isoformat(),
            )
            for t in txns
        ])
        existing = await db.execute(select(Holding).where(Holding.account_id == acc.id))
        existing_by_sec = {h.security_id: h for h in existing.scalars().all()}
        derived_by_sec = {h.security_id: h for h in new_derived}
        for sec_id, h in derived_by_sec.items():
            cur = existing_by_sec.get(sec_id)
            if cur:
                cur.quantity = h.quantity
                cur.acb_total_cad = h.acb_total_cad
            else:
                db.add(Holding(account_id=acc.id, security_id=sec_id,
                               quantity=h.quantity, acb_total_cad=h.acb_total_cad))
        for sec_id, cur in existing_by_sec.items():
            if sec_id not in derived_by_sec:
                await db.delete(cur)

    return result
