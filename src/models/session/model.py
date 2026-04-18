from dataclasses import dataclass
from typing import Optional
from models.base import BaseModel, row_get


@dataclass
class UserSession(BaseModel):
    id: str
    user_id: str
    login_method: str
    last_active_at: str
    is_revoked: int
    created_at: str
    device_info: Optional[str] = None
    ip_hash: Optional[str] = None
    country_code: Optional[str] = None
    expires_at: Optional[str] = None
    revoked_at: Optional[str] = None
    revoked_reason: Optional[str] = None

    def to_dict(self, scope: str = "public") -> dict:
        d = {
            "id": self.id,
            "device_info": self.device_info,
            "country_code": self.country_code,
            "login_method": self.login_method,
            "last_active_at": self.last_active_at,
            "is_revoked": self.is_revoked,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_row(cls, row) -> "UserSession":
        return cls(
            id=row_get(row, "id"),
            user_id=row_get(row, "user_id"),
            login_method=row_get(row, "login_method", "google_oauth"),
            last_active_at=row_get(row, "last_active_at", ""),
            is_revoked=row_get(row, "is_revoked", 0),
            created_at=row_get(row, "created_at", ""),
            device_info=row_get(row, "device_info"),
            ip_hash=row_get(row, "ip_hash"),
            country_code=row_get(row, "country_code"),
            expires_at=row_get(row, "expires_at"),
            revoked_at=row_get(row, "revoked_at"),
            revoked_reason=row_get(row, "revoked_reason"),
        )
