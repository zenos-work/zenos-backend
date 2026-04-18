from dataclasses import dataclass
from typing import Optional
from models.base import BaseModel, row_get


@dataclass
class CustomDomain(BaseModel):
    id: str
    domain: str
    resource_type: str
    verification_status: str
    verification_method: str
    verification_token: str
    ssl_status: str
    is_active: int
    created_at: str
    updated_at: str
    org_id: Optional[str] = None
    user_id: Optional[str] = None
    resource_id: Optional[str] = None
    verified_at: Optional[str] = None
    ssl_issued_at: Optional[str] = None
    ssl_expires_at: Optional[str] = None
    redirect_to: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "domain": self.domain,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "verification_status": self.verification_status,
            "verification_method": self.verification_method,
            "verification_token": self.verification_token,
            "ssl_status": self.ssl_status,
            "is_active": bool(self.is_active),
            "verified_at": self.verified_at,
            "ssl_issued_at": self.ssl_issued_at,
            "ssl_expires_at": self.ssl_expires_at,
            "redirect_to": self.redirect_to,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.org_id:
            d["org_id"] = self.org_id
        if self.user_id:
            d["user_id"] = self.user_id
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_row(cls, row) -> "CustomDomain":
        return cls(
            id=row_get(row, "id"),
            domain=row_get(row, "domain", ""),
            resource_type=row_get(row, "resource_type", "blog"),
            verification_status=row_get(row, "verification_status", "pending"),
            verification_method=row_get(row, "verification_method", "cname"),
            verification_token=row_get(row, "verification_token", ""),
            ssl_status=row_get(row, "ssl_status", "pending"),
            is_active=row_get(row, "is_active", 0),
            created_at=row_get(row, "created_at", ""),
            updated_at=row_get(row, "updated_at", ""),
            org_id=row_get(row, "org_id"),
            user_id=row_get(row, "user_id"),
            resource_id=row_get(row, "resource_id"),
            verified_at=row_get(row, "verified_at"),
            ssl_issued_at=row_get(row, "ssl_issued_at"),
            ssl_expires_at=row_get(row, "ssl_expires_at"),
            redirect_to=row_get(row, "redirect_to"),
        )
