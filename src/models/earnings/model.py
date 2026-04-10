from dataclasses import dataclass
from typing import Optional
from models.base import BaseModel, row_get


@dataclass
class AuthorEarnings(BaseModel):
    id: str
    author_id: str
    period_type: str
    period_start: str
    period_end: str
    total_earnings_cents: int
    net_earnings_cents: int
    platform_fee_cents: int
    status: str
    created_at: str
    updated_at: str
    org_id: Optional[str] = None
    premium_read_revenue_cents: int = 0
    tip_revenue_cents: int = 0
    course_revenue_cents: int = 0
    marketplace_revenue_cents: int = 0
    premium_reads_count: int = 0
    total_read_time_seconds: int = 0
    articles_contributing: int = 0

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "author_id": self.author_id,
            "period_type": self.period_type,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "premium_read_revenue_cents": self.premium_read_revenue_cents,
            "tip_revenue_cents": self.tip_revenue_cents,
            "course_revenue_cents": self.course_revenue_cents,
            "marketplace_revenue_cents": self.marketplace_revenue_cents,
            "total_earnings_cents": self.total_earnings_cents,
            "platform_fee_cents": self.platform_fee_cents,
            "net_earnings_cents": self.net_earnings_cents,
            "premium_reads_count": self.premium_reads_count,
            "total_read_time_seconds": self.total_read_time_seconds,
            "articles_contributing": self.articles_contributing,
            "status": self.status,
            "created_at": self.created_at,
        }
        if self.org_id:
            d["org_id"] = self.org_id
        return d

    @classmethod
    def from_row(cls, row) -> "AuthorEarnings":
        return cls(
            id=row_get(row, "id"),
            author_id=row_get(row, "author_id"),
            period_type=row_get(row, "period_type", "monthly"),
            period_start=row_get(row, "period_start", ""),
            period_end=row_get(row, "period_end", ""),
            total_earnings_cents=row_get(row, "total_earnings_cents", 0),
            net_earnings_cents=row_get(row, "net_earnings_cents", 0),
            platform_fee_cents=row_get(row, "platform_fee_cents", 0),
            status=row_get(row, "status", "pending"),
            created_at=row_get(row, "created_at", ""),
            updated_at=row_get(row, "updated_at", ""),
            org_id=row_get(row, "org_id"),
            premium_read_revenue_cents=row_get(row, "premium_read_revenue_cents", 0),
            tip_revenue_cents=row_get(row, "tip_revenue_cents", 0),
            course_revenue_cents=row_get(row, "course_revenue_cents", 0),
            marketplace_revenue_cents=row_get(row, "marketplace_revenue_cents", 0),
            premium_reads_count=row_get(row, "premium_reads_count", 0),
            total_read_time_seconds=row_get(row, "total_read_time_seconds", 0),
            articles_contributing=row_get(row, "articles_contributing", 0),
        )


@dataclass
class AuthorPayout(BaseModel):
    id: str
    author_id: str
    amount_cents: int
    currency: str
    payout_method: str
    status: str
    requested_at: str
    created_at: str
    stripe_transfer_id: Optional[str] = None
    external_reference: Optional[str] = None
    failure_reason: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    processed_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "author_id": self.author_id,
            "amount_cents": self.amount_cents,
            "currency": self.currency,
            "payout_method": self.payout_method,
            "status": self.status,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "requested_at": self.requested_at,
            "processed_at": self.processed_at,
            "completed_at": self.completed_at,
            "created_at": self.created_at,
        }
        if self.failure_reason:
            d["failure_reason"] = self.failure_reason
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_row(cls, row) -> "AuthorPayout":
        return cls(
            id=row_get(row, "id"),
            author_id=row_get(row, "author_id"),
            amount_cents=row_get(row, "amount_cents", 0),
            currency=row_get(row, "currency", "USD"),
            payout_method=row_get(row, "payout_method", "stripe"),
            status=row_get(row, "status", "pending"),
            requested_at=row_get(row, "requested_at", ""),
            created_at=row_get(row, "created_at", ""),
            stripe_transfer_id=row_get(row, "stripe_transfer_id"),
            external_reference=row_get(row, "external_reference"),
            failure_reason=row_get(row, "failure_reason"),
            period_start=row_get(row, "period_start"),
            period_end=row_get(row, "period_end"),
            processed_at=row_get(row, "processed_at"),
            completed_at=row_get(row, "completed_at"),
        )


@dataclass
class TipTransaction(BaseModel):
    id: str
    tipper_id: str
    author_id: str
    amount_cents: int
    currency: str
    platform_fee_cents: int
    net_amount_cents: int
    status: str
    created_at: str
    article_id: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    message: Optional[str] = None
    is_anonymous: int = 0

    def to_dict(self, scope: str = "public") -> dict:
        d = {
            "id": self.id,
            "article_id": self.article_id,
            "amount_cents": self.amount_cents,
            "currency": self.currency,
            "status": self.status,
            "message": self.message,
            "is_anonymous": bool(self.is_anonymous),
            "created_at": self.created_at,
        }
        if scope == "author":
            if not self.is_anonymous:
                d["tipper_id"] = self.tipper_id
            d["net_amount_cents"] = self.net_amount_cents
        elif scope == "tipper":
            d["author_id"] = self.author_id
            d["tipper_id"] = self.tipper_id
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_row(cls, row) -> "TipTransaction":
        return cls(
            id=row_get(row, "id"),
            tipper_id=row_get(row, "tipper_id"),
            author_id=row_get(row, "author_id"),
            amount_cents=row_get(row, "amount_cents", 0),
            currency=row_get(row, "currency", "USD"),
            platform_fee_cents=row_get(row, "platform_fee_cents", 0),
            net_amount_cents=row_get(row, "net_amount_cents", 0),
            status=row_get(row, "status", "completed"),
            created_at=row_get(row, "created_at", ""),
            article_id=row_get(row, "article_id"),
            stripe_payment_intent_id=row_get(row, "stripe_payment_intent_id"),
            message=row_get(row, "message"),
            is_anonymous=row_get(row, "is_anonymous", 0),
        )
