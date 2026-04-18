"""Phase 9 Step 33 — Marketplace models."""

import json
from dataclasses import dataclass


def _json_field(row, key, default=None):
    v = row.get(key)
    if v is None:
        return default if default is not None else []
    if isinstance(v, (dict, list)):
        return v
    try:
        return json.loads(v)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []


@dataclass
class MarketplaceItem:
    id: str = ""
    seller_id: str = ""
    org_id: str = ""
    name: str = ""
    slug: str = ""
    short_desc: str = ""
    long_desc: str = ""
    item_type: str = ""
    category: str = ""
    price_cents: int = 0
    currency: str = "USD"
    pricing_model: str = "one_time"
    preview_images: list = None
    asset_url: str = ""
    workflow_id: str = ""
    status: str = "draft"
    is_featured: bool = False
    download_count: int = 0
    purchase_count: int = 0
    rating_avg: float = 0.0
    rating_count: int = 0
    published_at: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if self.preview_images is None:
            self.preview_images = []

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            seller_id=row.get("seller_id", ""),
            org_id=row.get("org_id", "") or "",
            name=row.get("name", ""),
            slug=row.get("slug", ""),
            short_desc=row.get("short_desc", ""),
            long_desc=row.get("long_desc", "") or "",
            item_type=row.get("item_type", "") or "",
            category=row.get("category", ""),
            price_cents=int(row.get("price_cents", 0) or 0),
            currency=row.get("currency", "USD") or "USD",
            pricing_model=row.get("pricing_model", "one_time") or "one_time",
            preview_images=_json_field(row, "preview_images", []),
            asset_url=row.get("asset_url", "") or "",
            workflow_id=row.get("workflow_id", "") or "",
            status=row.get("status", "draft") or "draft",
            is_featured=bool(row.get("is_featured", 0)),
            download_count=int(row.get("download_count", 0) or 0),
            purchase_count=int(row.get("purchase_count", 0) or 0),
            rating_avg=float(row.get("rating_avg", 0) or 0),
            rating_count=int(row.get("rating_count", 0) or 0),
            published_at=row.get("published_at", "") or "",
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", "") or "",
        )

    def to_dict(self, scope="default"):
        return {
            "id": self.id,
            "seller_id": self.seller_id,
            "org_id": self.org_id,
            "name": self.name,
            "slug": self.slug,
            "short_desc": self.short_desc,
            "long_desc": self.long_desc,
            "item_type": self.item_type,
            "category": self.category,
            "price_cents": self.price_cents,
            "currency": self.currency,
            "pricing_model": self.pricing_model,
            "preview_images": self.preview_images,
            "asset_url": self.asset_url,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "is_featured": self.is_featured,
            "download_count": self.download_count,
            "purchase_count": self.purchase_count,
            "rating_avg": self.rating_avg,
            "rating_count": self.rating_count,
            "published_at": self.published_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class MarketplacePurchase:
    id: str = ""
    item_id: str = ""
    buyer_id: str = ""
    org_id: str = ""
    payment_id: str = ""
    price_paid_cents: int = 0
    currency: str = "USD"
    status: str = "completed"
    purchased_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            item_id=row.get("item_id", ""),
            buyer_id=row.get("buyer_id", ""),
            org_id=row.get("org_id", "") or "",
            payment_id=row.get("payment_id", "") or "",
            price_paid_cents=int(row.get("price_paid_cents", 0) or 0),
            currency=row.get("currency", "USD") or "USD",
            status=row.get("status", "completed") or "completed",
            purchased_at=row.get("purchased_at", ""),
        )

    def to_dict(self, scope="default"):
        return {
            "id": self.id,
            "item_id": self.item_id,
            "buyer_id": self.buyer_id,
            "org_id": self.org_id,
            "payment_id": self.payment_id,
            "price_paid_cents": self.price_paid_cents,
            "currency": self.currency,
            "status": self.status,
            "purchased_at": self.purchased_at,
        }


@dataclass
class MarketplaceReview:
    id: str = ""
    item_id: str = ""
    reviewer_id: str = ""
    rating: int = 0
    body: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            item_id=row.get("item_id", ""),
            reviewer_id=row.get("reviewer_id", ""),
            rating=int(row.get("rating", 0) or 0),
            body=row.get("body", "") or "",
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, scope="default"):
        return {
            "id": self.id,
            "item_id": self.item_id,
            "reviewer_id": self.reviewer_id,
            "rating": self.rating,
            "body": self.body,
            "created_at": self.created_at,
        }
