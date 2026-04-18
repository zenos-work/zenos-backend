from dataclasses import dataclass
from typing import Optional
import json
import hashlib
from models.base import BaseModel, row_get


VALID_CATEGORIES = {
    "general",
    "export",
    "workflow",
    "community",
    "marketplace",
    "analytics",
    "newsletter",
    "course",
    "billing",
    "enterprise",
}

VALID_TARGET_TYPES = {
    "global",
    "user_ids",
    "user_roles",
    "org_ids",
    "org_tiers",
    "membership_tiers",
    "percentage",
}


@dataclass
class FeatureFlag(BaseModel):
    id: str
    flag_key: str
    name: str
    category: str
    is_active: bool
    target_type: str
    targets: list
    rollout_pct: int
    created_by: str
    created_at: str
    updated_at: str
    description: Optional[str] = None
    metadata: Optional[dict] = None
    updated_by: Optional[str] = None

    def to_dict(self, scope: str = "public") -> dict:
        d = {
            "id": self.id,
            "flag_key": self.flag_key,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "is_active": self.is_active,
            "target_type": self.target_type,
            "targets": self.targets,
            "rollout_pct": self.rollout_pct,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if scope == "admin":
            d["metadata"] = self.metadata or {}
            d["created_by"] = self.created_by
            d["updated_by"] = self.updated_by
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_row(cls, row) -> "FeatureFlag":
        if row is None:
            return None
        raw_targets = row_get(row, "targets", "[]")
        targets = (
            json.loads(raw_targets) if isinstance(raw_targets, str) else raw_targets
        )
        raw_meta = row_get(row, "metadata", "{}")
        metadata = json.loads(raw_meta) if isinstance(raw_meta, str) else raw_meta
        return cls(
            id=row_get(row, "id"),
            flag_key=row_get(row, "flag_key"),
            name=row_get(row, "name"),
            description=row_get(row, "description"),
            category=row_get(row, "category", "general"),
            is_active=bool(row_get(row, "is_active", 0)),
            target_type=row_get(row, "target_type", "global"),
            targets=targets,
            rollout_pct=int(row_get(row, "rollout_pct", 0)),
            metadata=metadata,
            created_by=row_get(row, "created_by", ""),
            updated_by=row_get(row, "updated_by"),
            created_at=row_get(row, "created_at", ""),
            updated_at=row_get(row, "updated_at", ""),
        )

    def evaluate(
        self,
        user_id=None,
        user_role=None,
        org_id=None,
        org_tier=None,
        membership_tier=None,
    ) -> bool:
        """Evaluate whether this flag is enabled for the given context."""
        if not self.is_active:
            return False
        tt = self.target_type
        if tt == "global":
            return True
        if tt == "user_ids":
            return user_id in self.targets
        if tt == "user_roles":
            return user_role in self.targets
        if tt == "org_ids":
            return org_id in self.targets
        if tt == "org_tiers":
            return org_tier in self.targets
        if tt == "membership_tiers":
            return membership_tier in self.targets
        if tt == "percentage":
            if not user_id:
                return False
            h = hashlib.md5(f"{user_id}:{self.flag_key}".encode()).hexdigest()
            return (int(h[:8], 16) % 100) < self.rollout_pct
        return False
