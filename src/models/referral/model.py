"""Phase 9 Step 34 — Referral models."""

import json
from dataclasses import dataclass


def _json_field(row, key, default=None):
    v = row.get(key)
    if v is None:
        return default if default is not None else {}
    if isinstance(v, (dict, list)):
        return v
    try:
        return json.loads(v)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else {}


@dataclass
class ReferralCode:
    id: str = ""
    user_id: str = ""
    code: str = ""
    total_clicks: int = 0
    total_signups: int = 0
    total_conversions: int = 0
    reward_credits: int = 0
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            user_id=row.get("user_id", ""),
            code=row.get("code", ""),
            total_clicks=int(row.get("total_clicks", 0) or 0),
            total_signups=int(row.get("total_signups", 0) or 0),
            total_conversions=int(row.get("total_conversions", 0) or 0),
            reward_credits=int(row.get("reward_credits", 0) or 0),
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, scope="default"):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "code": self.code,
            "total_clicks": self.total_clicks,
            "total_signups": self.total_signups,
            "total_conversions": self.total_conversions,
            "reward_credits": self.reward_credits,
            "created_at": self.created_at,
        }


@dataclass
class ReferralEvent:
    id: str = ""
    referral_code_id: str = ""
    event_type: str = ""
    referred_user_id: str = ""
    metadata: dict = None
    created_at: str = ""

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            referral_code_id=row.get("referral_code_id", ""),
            event_type=row.get("event_type", ""),
            referred_user_id=row.get("referred_user_id", "") or "",
            metadata=_json_field(row, "metadata", {}),
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, scope="default"):
        return {
            "id": self.id,
            "referral_code_id": self.referral_code_id,
            "event_type": self.event_type,
            "referred_user_id": self.referred_user_id,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }
