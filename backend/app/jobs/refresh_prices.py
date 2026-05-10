"""Daily price refresh job stub. Wire to Cloud Scheduler later."""

from __future__ import annotations

import asyncio
from datetime import date


async def refresh_prices(as_of: date | None = None) -> int:
    """Pull latest close prices from Yahoo for every security in DB.

    Returns count of prices written. Currently a no-op placeholder.
    """
    _ = as_of or date.today()
    await asyncio.sleep(0)
    return 0
