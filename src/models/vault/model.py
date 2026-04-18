"""Phase 11 Step 44 — Credential vault models."""

from dataclasses import dataclass


@dataclass
class VaultSecret:
    id: str = ""
    org_id: str = ""
    name: str = ""
    secret_type: str = "generic"  # generic, oauth_token, api_key, webhook_secret
    provider: str = "cloudflare"
    key_ref: str = ""
    is_active: bool = True
    last_rotated_at: str = ""
    expires_at: str = ""
    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""
    metadata: str = "{}"

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id", ""),
            name=row.get("name", ""),
            secret_type=row.get("secret_type", "generic") or "generic",
            provider=row.get("provider", "cloudflare") or "cloudflare",
            key_ref=row.get("key_ref", "") or "",
            is_active=bool(row.get("is_active", 1)),
            last_rotated_at=row.get("last_rotated_at", "") or "",
            expires_at=row.get("expires_at", "") or "",
            created_by=row.get("created_by", "") or "",
            created_at=row.get("created_at", "") or "",
            updated_at=row.get("updated_at", "") or "",
            metadata=row.get("metadata", "{}") or "{}",
        )

    def to_dict(self, scope="default"):
        d = {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "secret_type": self.secret_type,
            "provider": self.provider,
            "key_ref": self.key_ref,
            "is_active": self.is_active,
            "last_rotated_at": self.last_rotated_at,
            "expires_at": self.expires_at,
        }
        if scope == "admin":
            d["created_by"] = self.created_by
            d["created_at"] = self.created_at
            d["updated_at"] = self.updated_at
            d["metadata"] = self.metadata
        return d


@dataclass
class VaultWriteQuota:
    """Tracks daily write budget per org (max 50 on free tier)."""

    org_id: str = ""
    date: str = ""
    write_count: int = 0
    max_writes: int = 50

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            org_id=row.get("org_id", ""),
            date=row.get("date", ""),
            write_count=int(row.get("write_count", 0)),
            max_writes=int(row.get("max_writes", 50)),
        )

    def to_dict(self, scope="default"):
        return {
            "org_id": self.org_id,
            "date": self.date,
            "write_count": self.write_count,
            "max_writes": self.max_writes,
            "remaining": max(0, self.max_writes - self.write_count),
        }
