"""Phase 10 Step 40 — Alert rule model."""

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
class AlertRule:
    id: str = ""
    org_id: str = ""
    created_by: str = ""
    name: str = ""
    alert_type: str = ""
    config: dict = None
    threshold_value: float = 0.0
    comparison: str = ""
    notify_channels: list = None
    notify_user_ids: list = None
    cooldown_minutes: int = 60
    is_active: bool = True
    last_triggered_at: str = ""
    trigger_count: int = 0
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if self.config is None:
            self.config = {}
        if self.notify_channels is None:
            self.notify_channels = ["in_app"]
        if self.notify_user_ids is None:
            self.notify_user_ids = []

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id", ""),
            created_by=row.get("created_by", ""),
            name=row.get("name", ""),
            alert_type=row.get("alert_type", ""),
            config=_json_field(row, "config", {}),
            threshold_value=float(row.get("threshold_value", 0) or 0),
            comparison=row.get("comparison", "") or "",
            notify_channels=_json_field(row, "notify_channels", ["in_app"]),
            notify_user_ids=_json_field(row, "notify_user_ids", []),
            cooldown_minutes=int(row.get("cooldown_minutes", 60) or 60),
            is_active=bool(row.get("is_active", 1)),
            last_triggered_at=row.get("last_triggered_at", "") or "",
            trigger_count=int(row.get("trigger_count", 0) or 0),
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", "") or "",
        )

    def to_dict(self, scope="default"):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "created_by": self.created_by,
            "name": self.name,
            "alert_type": self.alert_type,
            "config": self.config,
            "threshold_value": self.threshold_value,
            "comparison": self.comparison,
            "notify_channels": self.notify_channels,
            "notify_user_ids": self.notify_user_ids,
            "cooldown_minutes": self.cooldown_minutes,
            "is_active": self.is_active,
            "last_triggered_at": self.last_triggered_at,
            "trigger_count": self.trigger_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
