from dataclasses import dataclass
from typing import Optional
from models.base import BaseModel, row_get


@dataclass
class AuditLogEntry(BaseModel):
    id: str
    action: str
    created_at: str
    org_id: Optional[str] = None
    actor_id: Optional[str] = None
    actor_ip: Optional[str] = None
    resource: Optional[str] = None
    resource_id: Optional[str] = None
    payload: Optional[str] = None

    def to_dict(self, scope: str = "public") -> dict:
        d = {
            "id": self.id,
            "action": self.action,
            "created_at": self.created_at,
            "actor_id": self.actor_id,
            "resource": self.resource,
            "resource_id": self.resource_id,
        }
        if scope == "admin":
            d["org_id"] = self.org_id
            d["actor_ip"] = self.actor_ip
            d["payload"] = self.payload
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_row(cls, row) -> "AuditLogEntry":
        return cls(
            id=row_get(row, "id"),
            action=row_get(row, "action", ""),
            created_at=row_get(row, "created_at", ""),
            org_id=row_get(row, "org_id"),
            actor_id=row_get(row, "actor_id"),
            actor_ip=row_get(row, "actor_ip"),
            resource=row_get(row, "resource"),
            resource_id=row_get(row, "resource_id"),
            payload=row_get(row, "payload"),
        )


@dataclass
class ApiKey(BaseModel):
    id: str
    name: str
    key_prefix: str
    scopes: str
    created_by: str
    created_at: str
    org_id: Optional[str] = None
    user_id: Optional[str] = None
    key_hash: Optional[str] = None
    last_used_at: Optional[str] = None
    expires_at: Optional[str] = None
    revoked_at: Optional[str] = None

    def to_dict(self, scope: str = "public") -> dict:
        d = {
            "id": self.id,
            "name": self.name,
            "key_prefix": self.key_prefix,
            "scopes": self.scopes,
            "created_at": self.created_at,
        }
        if scope == "admin":
            d["org_id"] = self.org_id
            d["user_id"] = self.user_id
            d["created_by"] = self.created_by
            d["last_used_at"] = self.last_used_at
            d["expires_at"] = self.expires_at
            d["revoked_at"] = self.revoked_at
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_row(cls, row) -> "ApiKey":
        return cls(
            id=row_get(row, "id"),
            name=row_get(row, "name", ""),
            key_prefix=row_get(row, "key_prefix", ""),
            scopes=row_get(row, "scopes", '["read"]'),
            created_by=row_get(row, "created_by", ""),
            created_at=row_get(row, "created_at", ""),
            org_id=row_get(row, "org_id"),
            user_id=row_get(row, "user_id"),
            key_hash=row_get(row, "key_hash"),
            last_used_at=row_get(row, "last_used_at"),
            expires_at=row_get(row, "expires_at"),
            revoked_at=row_get(row, "revoked_at"),
        )


@dataclass
class SsoConfig(BaseModel):
    id: str
    org_id: str
    provider: str
    metadata: str
    is_enabled: int
    created_by: str
    created_at: str
    updated_at: str

    def to_dict(self, scope: str = "public") -> dict:
        d = {
            "id": self.id,
            "org_id": self.org_id,
            "provider": self.provider,
            "is_enabled": self.is_enabled,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if scope == "admin":
            d["metadata"] = self.metadata
            d["created_by"] = self.created_by
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_row(cls, row) -> "SsoConfig":
        return cls(
            id=row_get(row, "id"),
            org_id=row_get(row, "org_id", ""),
            provider=row_get(row, "provider", ""),
            metadata=row_get(row, "metadata", "{}"),
            is_enabled=row_get(row, "is_enabled", 0),
            created_by=row_get(row, "created_by", ""),
            created_at=row_get(row, "created_at", ""),
            updated_at=row_get(row, "updated_at", ""),
        )
