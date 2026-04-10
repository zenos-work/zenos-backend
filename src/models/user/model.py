from dataclasses import dataclass
from typing import Optional
from models.base import BaseModel, row_get
from models.common.enums import Scope

_PUBLIC_FIELDS = {
    "id",
    "name",
    "role",
    "avatar_url",
    "created_at",
    "membership_tier",
    "handle",
    "bio",
    "website_url",
    "social_links",
    "location",
    "cover_image_url",
    "pronouns",
    "tagline",
}
_PRIVATE_FIELDS = _PUBLIC_FIELDS | {
    "email",
    "is_active",
    "updated_at",
    "terms_accepted_at",
    "membership_status",
    "subscription_started_at",
    "subscription_expires_at",
    "payout_method",
    "payout_email",
    "payout_min_cents",
}
_ADMIN_FIELDS = _PRIVATE_FIELDS | {
    "google_id",
    "stripe_customer_id",
    "stripe_subscription_id",
    "stripe_connect_id",
    "premium_read_count",
    "last_premium_read_at",
}

_SCOPE_MAP = {
    Scope.PUBLIC: _PUBLIC_FIELDS,
    Scope.PRIVATE: _PRIVATE_FIELDS,
    Scope.ADMIN: _ADMIN_FIELDS,
}


@dataclass
class User(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: int
    created_at: str
    updated_at: str
    avatar_url: Optional[str] = None
    google_id: Optional[str] = None
    terms_accepted_at: Optional[str] = None
    membership_tier: str = "free"
    membership_status: str = "inactive"
    subscription_started_at: Optional[str] = None
    subscription_expires_at: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    premium_read_count: int = 0
    last_premium_read_at: Optional[str] = None
    # Profile fields
    handle: Optional[str] = None
    bio: Optional[str] = None
    website_url: Optional[str] = None
    social_links: Optional[str] = None
    location: Optional[str] = None
    cover_image_url: Optional[str] = None
    pronouns: Optional[str] = None
    tagline: Optional[str] = None
    # Payout fields
    payout_method: str = "stripe"
    payout_email: Optional[str] = None
    payout_min_cents: int = 5000
    stripe_connect_id: Optional[str] = None

    def to_dict(self, scope: str = Scope.PUBLIC) -> dict:
        allowed = _SCOPE_MAP.get(scope, _PUBLIC_FIELDS)
        return {
            k: v
            for k, v in {
                "id": self.id,
                "email": self.email,
                "name": self.name,
                "role": self.role,
                "is_active": self.is_active,
                "avatar_url": self.avatar_url,
                "google_id": self.google_id,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "terms_accepted_at": self.terms_accepted_at,
                "membership_tier": self.membership_tier,
                "membership_status": self.membership_status,
                "subscription_started_at": self.subscription_started_at,
                "subscription_expires_at": self.subscription_expires_at,
                "stripe_customer_id": self.stripe_customer_id,
                "stripe_subscription_id": self.stripe_subscription_id,
                "premium_read_count": self.premium_read_count,
                "last_premium_read_at": self.last_premium_read_at,
                "handle": self.handle,
                "bio": self.bio,
                "website_url": self.website_url,
                "social_links": self.social_links,
                "location": self.location,
                "cover_image_url": self.cover_image_url,
                "pronouns": self.pronouns,
                "tagline": self.tagline,
                "payout_method": self.payout_method,
                "payout_email": self.payout_email,
                "payout_min_cents": self.payout_min_cents,
                "stripe_connect_id": self.stripe_connect_id,
            }.items()
            if k in allowed and v is not None
        }

    @classmethod
    def from_row(cls, row) -> "User":
        return cls(
            id=row_get(row, "id"),
            email=row_get(row, "email", ""),
            name=row_get(row, "name", ""),
            role=row_get(row, "role", "READER"),
            is_active=row_get(row, "is_active", 1),
            created_at=row_get(row, "created_at", ""),
            updated_at=row_get(row, "updated_at", ""),
            avatar_url=row_get(row, "avatar_url"),
            google_id=row_get(row, "google_id"),
            terms_accepted_at=row_get(row, "terms_accepted_at"),
            membership_tier=row_get(row, "membership_tier", "free"),
            membership_status=row_get(row, "membership_status", "inactive"),
            subscription_started_at=row_get(row, "subscription_started_at"),
            subscription_expires_at=row_get(row, "subscription_expires_at"),
            stripe_customer_id=row_get(row, "stripe_customer_id"),
            stripe_subscription_id=row_get(row, "stripe_subscription_id"),
            premium_read_count=row_get(row, "premium_read_count", 0),
            last_premium_read_at=row_get(row, "last_premium_read_at"),
            handle=row_get(row, "handle"),
            bio=row_get(row, "bio"),
            website_url=row_get(row, "website_url"),
            social_links=row_get(row, "social_links"),
            location=row_get(row, "location"),
            cover_image_url=row_get(row, "cover_image_url"),
            pronouns=row_get(row, "pronouns"),
            tagline=row_get(row, "tagline"),
            payout_method=row_get(row, "payout_method", "stripe"),
            payout_email=row_get(row, "payout_email"),
            payout_min_cents=row_get(row, "payout_min_cents", 5000),
            stripe_connect_id=row_get(row, "stripe_connect_id"),
        )
