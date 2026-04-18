from dataclasses import dataclass
from typing import Optional
from models.base import BaseModel, row_get


VALID_ADD_ON_TYPES = (
    "workflow_builder",
    "connector_suite",
    "digital_marketing",
    "advanced_analytics",
    "lead_generation",
    "custom_domains",
    "courses",
    "community_marketplace",
)

TIER_HIERARCHY = {
    "basic": 0,
    "standard": 0,
    "single": 0,
    "pro": 1,
    "premium": 1,
    "unlimited": 2,
}


@dataclass
class OrgAddOn(BaseModel):
    id: str
    org_id: str
    add_on_type: str
    tier: str
    is_active: int
    enabled_by: str
    limits: str
    started_at: str
    created_at: str
    updated_at: str
    stripe_subscription_id: Optional[str] = None
    trial_ends_at: Optional[str] = None
    expires_at: Optional[str] = None

    def to_dict(self, scope: str = "public") -> dict:
        d = {
            "id": self.id,
            "org_id": self.org_id,
            "add_on_type": self.add_on_type,
            "tier": self.tier,
            "is_active": self.is_active,
            "limits": self.limits,
            "started_at": self.started_at,
            "created_at": self.created_at,
        }
        if scope == "admin":
            d["enabled_by"] = self.enabled_by
            d["stripe_subscription_id"] = self.stripe_subscription_id
            d["trial_ends_at"] = self.trial_ends_at
            d["expires_at"] = self.expires_at
            d["updated_at"] = self.updated_at
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_row(cls, row) -> "OrgAddOn":
        return cls(
            id=row_get(row, "id"),
            org_id=row_get(row, "org_id", ""),
            add_on_type=row_get(row, "add_on_type", ""),
            tier=row_get(row, "tier", "basic"),
            is_active=row_get(row, "is_active", 1),
            enabled_by=row_get(row, "enabled_by", ""),
            limits=row_get(row, "limits", "{}"),
            started_at=row_get(row, "started_at", ""),
            created_at=row_get(row, "created_at", ""),
            updated_at=row_get(row, "updated_at", ""),
            stripe_subscription_id=row_get(row, "stripe_subscription_id"),
            trial_ends_at=row_get(row, "trial_ends_at"),
            expires_at=row_get(row, "expires_at"),
        )


def require_add_on(add_on, min_tier=None):
    """Validate add-on is active and tier is sufficient. Raises PermissionError."""
    if not add_on or not add_on.is_active:
        raise PermissionError("Add-on not active")
    if min_tier:
        current = TIER_HIERARCHY.get(add_on.tier, 0)
        required = TIER_HIERARCHY.get(min_tier, 0)
        if current < required:
            raise PermissionError(f"Tier '{min_tier}' or higher required")
    return add_on
