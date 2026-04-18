from typing import Optional
from api.earnings.repository import EarningsRepository
from api.earnings.distribution import calculate_distribution
from utils.helpers import new_id, paginate

PLATFORM_FEE_RATE = 0.10  # 10% platform fee on tips


class EarningsService:
    def __init__(self, env, ctx=None):
        self._repo = EarningsRepository(env.DB, ctx)

    async def get_earnings(self, author_id: str, page: int = 1, limit: int = 20):
        _limit, offset = paginate(page, limit)
        items = await self._repo.find_earnings_by_author(author_id, _limit, offset)
        total = await self._repo.count_earnings_by_author(author_id)
        summary = await self._repo.earnings_summary(author_id)
        return {
            "earnings": [e.to_dict() for e in items],
            "summary": summary,
            "pagination": {
                "page": page,
                "limit": _limit,
                "total": total,
                "pages": (total + _limit - 1) // _limit if _limit else 0,
            },
        }

    async def get_payouts(self, author_id: str, page: int = 1, limit: int = 20):
        _limit, offset = paginate(page, limit)
        items = await self._repo.find_payouts_by_author(author_id, _limit, offset)
        total = await self._repo.count_payouts_by_author(author_id)
        return {
            "payouts": [p.to_dict() for p in items],
            "pagination": {
                "page": page,
                "limit": _limit,
                "total": total,
                "pages": (total + _limit - 1) // _limit if _limit else 0,
            },
        }

    async def request_payout(
        self,
        author_id: str,
        amount_cents: int,
        currency: str = "USD",
        payout_method: str = "stripe",
        period_start: Optional[str] = None,
        period_end: Optional[str] = None,
    ) -> str:
        if amount_cents <= 0:
            raise ValueError("Amount must be positive")
        if payout_method not in {"stripe", "paypal", "bank_transfer", "manual"}:
            raise ValueError(f"Invalid payout_method: {payout_method}")
        has_pending = await self._repo.has_pending_payout(author_id)
        if has_pending:
            raise ValueError("A pending payout already exists")
        pid = new_id()
        await self._repo.create_payout_request(
            pid,
            author_id,
            amount_cents,
            currency,
            payout_method,
            period_start,
            period_end,
        )
        return pid

    async def send_tip(
        self,
        tipper_id: str,
        author_id: str,
        amount_cents: int,
        article_id: Optional[str] = None,
        currency: str = "USD",
        message: Optional[str] = None,
        is_anonymous: bool = False,
    ) -> str:
        if amount_cents <= 0:
            raise ValueError("Tip amount must be positive")
        if tipper_id == author_id:
            raise ValueError("Cannot tip yourself")
        fee = int(amount_cents * PLATFORM_FEE_RATE)
        net = amount_cents - fee
        tid = new_id()
        await self._repo.create_tip(
            tid,
            tipper_id,
            author_id,
            amount_cents,
            fee,
            net,
            article_id,
            currency,
            message,
            1 if is_anonymous else 0,
        )
        return tid

    async def get_tips_received(self, author_id: str, page: int = 1, limit: int = 20):
        _limit, offset = paginate(page, limit)
        items = await self._repo.find_tips_received(author_id, _limit, offset)
        total = await self._repo.count_tips_received(author_id)
        return {
            "tips": [t.to_dict(scope="author") for t in items],
            "pagination": {
                "page": page,
                "limit": _limit,
                "total": total,
                "pages": (total + _limit - 1) // _limit if _limit else 0,
            },
        }

    # ── Phase 12 Step 46: Distribution ──
    async def calculate_monthly_distribution(
        self,
        period_start: str,
        period_end: str,
        active_subscribers: int,
        payout_ratio: float = 0.70,
        min_payout_cents: int = 2500,
    ) -> dict:
        reads = await self._repo.premium_reads_for_period(period_start, period_end)
        result = calculate_distribution(
            reads=reads,
            active_subscribers=active_subscribers,
            payout_ratio=payout_ratio,
            contribution_cents=500,
            min_payout_cents=min_payout_cents,
        )

        # Aggregate supporting metrics per author for persistent earnings rows.
        metrics = {}
        for r in reads:
            aid = r.get("author_id", "")
            if not aid:
                continue
            m = metrics.setdefault(
                aid,
                {
                    "reads_count": 0,
                    "total_seconds": 0,
                    "articles": set(),
                },
            )
            m["reads_count"] += 1
            m["total_seconds"] += int(r.get("read_time_seconds", 0) or 0)
            article_id = r.get("article_id", "")
            if article_id:
                m["articles"].add(article_id)

        persisted_rows = 0
        payouts_created = 0
        for author_id, amount_cents in result["author_shares"].items():
            m = metrics.get(
                author_id, {"reads_count": 0, "total_seconds": 0, "articles": set()}
            )
            await self._repo.upsert_distribution_row(
                earning_id=new_id(),
                author_id=author_id,
                period_start=period_start,
                period_end=period_end,
                amount_cents=amount_cents,
                premium_reads_count=m["reads_count"],
                total_read_time_seconds=m["total_seconds"],
                articles_contributing=len(m["articles"]),
            )
            persisted_rows += 1

        for author_id, amount_cents in result["eligible_payouts"].items():
            await self._repo.create_pending_payout(
                payout_id=new_id(),
                author_id=author_id,
                amount_cents=amount_cents,
                period_start=period_start,
                period_end=period_end,
            )
            payouts_created += 1

        return {
            "period_start": period_start,
            "period_end": period_end,
            "active_subscribers": active_subscribers,
            "payout_ratio": payout_ratio,
            "distribution": result,
            "persisted_rows": persisted_rows,
            "pending_payouts_created": payouts_created,
        }

    async def distribution_report(self, period_start: str):
        rows = await self._repo.earnings_by_period(period_start)
        return {
            "period_start": period_start,
            "authors": [r.to_dict() for r in rows],
            "authors_count": len(rows),
            "total_earnings_cents": sum(r.total_earnings_cents for r in rows),
        }

    async def my_breakdown(self, author_id: str, period_start: str):
        rows = await self._repo.earnings_by_period(period_start)
        mine = [r for r in rows if r.author_id == author_id]
        return {
            "period_start": period_start,
            "breakdown": [r.to_dict() for r in mine],
            "total_earnings_cents": sum(r.total_earnings_cents for r in mine),
        }
