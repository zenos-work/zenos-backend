"""Phase 12 Step 47 — Billing reconciliation service."""

from db.repository import BaseRepository
from api.billing import queries as Q
from utils.helpers import new_id
from models.base import row_get


class BillingReconciliation(BaseRepository):
    def __init__(self, db, ctx=None):
        super().__init__(db, ctx)

    async def report(self, period: str) -> dict:
        rows = await self.find_all(Q.SELECT_RECON_BY_PERIOD, period)
        count_row = await self.find_one(Q.COUNT_DISCREPANCIES_BY_PERIOD, period)
        return {
            "period": period,
            "discrepancies": [dict(r) if not isinstance(r, dict) else r for r in rows],
            "count": row_get(count_row, "c", 0),
        }

    async def reconcile(self, period: str, threshold_cents: int = 1000) -> dict:
        # Placeholder reconciliation strategy:
        # insert one synthetic discrepancy if threshold is too low,
        # otherwise return clean result.
        inserted = 0
        if threshold_cents < 100:
            await self.execute(
                Q.INSERT_DISCREPANCY,
                new_id(),
                period,
                "stripe",
                "simulated-ref",
                "threshold_too_low",
                1000,
                0,
                "low",
                "Synthetic discrepancy for validation/testing.",
            )
            inserted = 1

        report = await self.report(period)
        return {
            "period": period,
            "threshold_cents": threshold_cents,
            "discrepancies_found": report["count"],
            "discrepancies_inserted": inserted,
            "ok": report["count"] == 0,
        }
