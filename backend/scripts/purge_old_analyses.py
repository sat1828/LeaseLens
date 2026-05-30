#!/usr/bin/env python3
"""
MISSING-01: 90-day auto-purge script.
The purge_after column is set on every analysis at creation time.
This script hard-deletes rows where purge_after < NOW().

Run daily via cron:
  0 3 * * * cd /app && python scripts/purge_old_analyses.py

Or add as a Railway Cron service:
  Schedule: 0 3 * * *
  Command: python /app/scripts/purge_old_analyses.py
"""
import asyncio
import sys
import os

# Allow running from project root or scripts/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timezone
from sqlalchemy import delete, func, select
from app.db.session import AsyncSessionLocal, engine
from app.models.analysis import Analysis
from app.core.logging import log, setup_logging


async def purge_expired_analyses() -> int:
    """Hard-delete analyses past their purge_after date. Returns count deleted."""
    async with AsyncSessionLocal() as db:
        # Count first so we can log accurately
        count_result = await db.execute(
            select(func.count(Analysis.id)).where(
                Analysis.purge_after < datetime.now(timezone.utc),
                Analysis.purge_after.isnot(None),
                Analysis.is_deleted != 2,  # 2 = already purged
            )
        )
        eligible = count_result.scalar_one()

        if eligible == 0:
            log.info("purge.nothing_to_purge")
            return 0

        # Hard delete
        result = await db.execute(
            delete(Analysis).where(
                Analysis.purge_after < datetime.now(timezone.utc),
                Analysis.purge_after.isnot(None),
            )
        )
        await db.commit()
        count = result.rowcount
        log.info("purge.complete", deleted_count=count)
        return count


async def main() -> None:
    setup_logging()
    log.info("purge.start", timestamp=datetime.now(timezone.utc).isoformat())
    count = await purge_expired_analyses()
    print(f"[LeaseLens Purge] Deleted {count} expired analyses.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
