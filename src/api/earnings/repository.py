from typing import Optional, List
from db.repository import BaseRepository
from api.earnings import queries as Q
from models.earnings.model import AuthorEarnings, AuthorPayout, TipTransaction
from models.base import row_get


class EarningsRepository(BaseRepository):
    # ── Author Earnings ──
    async def find_earnings_by_author(
        self, author_id: str, limit: int, offset: int
    ) -> List[AuthorEarnings]:
        rows = await self.find_all(
            Q.SELECT_EARNINGS_BY_AUTHOR, author_id, limit, offset
        )
        return self.map_many(rows, AuthorEarnings)

    async def count_earnings_by_author(self, author_id: str) -> int:
        row = await self.find_one(Q.COUNT_EARNINGS_BY_AUTHOR, author_id)
        return row_get(row, "c", 0)

    async def earnings_summary(self, author_id: str) -> dict:
        row = await self.find_one(Q.SELECT_EARNINGS_SUMMARY, author_id)
        return {
            "total_earnings_cents": row_get(row, "total_earnings", 0),
            "net_earnings_cents": row_get(row, "net_earnings", 0),
            "total_fees_cents": row_get(row, "total_fees", 0),
            "total_reads": row_get(row, "total_reads", 0),
        }

    # ── Author Payouts ──
    async def find_payouts_by_author(
        self, author_id: str, limit: int, offset: int
    ) -> List[AuthorPayout]:
        rows = await self.find_all(Q.SELECT_PAYOUTS_BY_AUTHOR, author_id, limit, offset)
        return self.map_many(rows, AuthorPayout)

    async def count_payouts_by_author(self, author_id: str) -> int:
        row = await self.find_one(Q.COUNT_PAYOUTS_BY_AUTHOR, author_id)
        return row_get(row, "c", 0)

    async def has_pending_payout(self, author_id: str) -> bool:
        row = await self.find_one(Q.SELECT_PENDING_PAYOUT, author_id)
        return row is not None

    async def create_payout_request(
        self,
        payout_id: str,
        author_id: str,
        amount_cents: int,
        currency: str = "USD",
        payout_method: str = "stripe",
        period_start: Optional[str] = None,
        period_end: Optional[str] = None,
    ) -> None:
        await self.execute(
            Q.INSERT_PAYOUT_REQUEST,
            payout_id,
            author_id,
            amount_cents,
            currency,
            payout_method,
            period_start or "",
            period_end or "",
        )

    # ── Tips ──
    async def create_tip(
        self,
        tip_id: str,
        tipper_id: str,
        author_id: str,
        amount_cents: int,
        platform_fee_cents: int = 0,
        net_amount_cents: int = 0,
        article_id: Optional[str] = None,
        currency: str = "USD",
        message: Optional[str] = None,
        is_anonymous: int = 0,
    ) -> None:
        await self.execute(
            Q.INSERT_TIP,
            tip_id,
            tipper_id,
            author_id,
            article_id or "",
            amount_cents,
            currency,
            platform_fee_cents,
            net_amount_cents,
            message or "",
            is_anonymous,
        )

    async def find_tips_received(
        self, author_id: str, limit: int, offset: int
    ) -> List[TipTransaction]:
        rows = await self.find_all(Q.SELECT_TIPS_RECEIVED, author_id, limit, offset)
        return self.map_many(rows, TipTransaction)

    async def count_tips_received(self, author_id: str) -> int:
        row = await self.find_one(Q.COUNT_TIPS_RECEIVED, author_id)
        return row_get(row, "c", 0)

    # ── Phase 12 Step 46: Distribution ──
    async def premium_reads_for_period(
        self, period_start: str, period_end: str
    ) -> list[dict]:
        rows = await self.find_all(
            Q.SELECT_PREMIUM_READS_FOR_PERIOD, period_start, period_end
        )
        return [dict(r) if not isinstance(r, dict) else r for r in rows]

    async def earnings_by_period(self, period_start: str) -> List[AuthorEarnings]:
        rows = await self.find_all(Q.SELECT_EARNINGS_BY_PERIOD, period_start)
        return self.map_many(rows, AuthorEarnings)

    async def upsert_distribution_row(
        self,
        earning_id: str,
        author_id: str,
        period_start: str,
        period_end: str,
        amount_cents: int,
        premium_reads_count: int,
        total_read_time_seconds: int,
        articles_contributing: int,
    ) -> None:
        await self.execute(
            Q.UPSERT_AUTHOR_EARNINGS_DISTRIBUTION,
            earning_id,
            author_id,
            period_start,
            period_end,
            amount_cents,
            amount_cents,
            amount_cents,
            premium_reads_count,
            total_read_time_seconds,
            articles_contributing,
        )

    async def create_pending_payout(
        self,
        payout_id: str,
        author_id: str,
        amount_cents: int,
        period_start: str,
        period_end: str,
    ) -> None:
        await self.execute(
            Q.INSERT_PENDING_PAYOUT,
            payout_id,
            author_id,
            amount_cents,
            period_start,
            period_end,
        )
