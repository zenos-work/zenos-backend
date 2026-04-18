"""Phase 10 Step 36 — Notification preference & push subscription models."""

from dataclasses import dataclass


@dataclass
class NotificationPreference:
    user_id: str = ""
    notification_type: str = ""
    channel: str = "in_app"
    is_enabled: bool = True

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            user_id=row.get("user_id", ""),
            notification_type=row.get("notification_type", ""),
            channel=row.get("channel", "in_app") or "in_app",
            is_enabled=bool(row.get("is_enabled", 1)),
        )

    def to_dict(self, scope="default"):
        return {
            "user_id": self.user_id,
            "notification_type": self.notification_type,
            "channel": self.channel,
            "is_enabled": self.is_enabled,
        }


@dataclass
class PushSubscription:
    id: str = ""
    user_id: str = ""
    platform: str = "web"
    endpoint: str = ""
    p256dh_key: str = ""
    auth_key: str = ""
    device_name: str = ""
    is_active: bool = True
    created_at: str = ""
    last_used_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            user_id=row.get("user_id", ""),
            platform=row.get("platform", "web") or "web",
            endpoint=row.get("endpoint", ""),
            p256dh_key=row.get("p256dh_key", ""),
            auth_key=row.get("auth_key", ""),
            device_name=row.get("device_name", "") or "",
            is_active=bool(row.get("is_active", 1)),
            created_at=row.get("created_at", ""),
            last_used_at=row.get("last_used_at", "") or "",
        )

    def to_dict(self, scope="default"):
        d = {
            "id": self.id,
            "user_id": self.user_id,
            "platform": self.platform,
            "endpoint": self.endpoint,
            "device_name": self.device_name,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "last_used_at": self.last_used_at,
        }
        if scope == "admin":
            d["p256dh_key"] = self.p256dh_key
            d["auth_key"] = self.auth_key
        return d
