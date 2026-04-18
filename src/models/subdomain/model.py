"""Phase 11 Step 41 — Subdomain provisioning models."""

from dataclasses import dataclass


@dataclass
class SubdomainConfig:
    org_id: str = ""
    subdomain: str = ""
    is_active: bool = True
    provisioned_at: str = ""
    provisioned_by: str = ""
    custom_domain: str = ""
    ssl_status: str = "pending"
    settings: str = "{}"
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            org_id=row.get("org_id", ""),
            subdomain=row.get("subdomain", ""),
            is_active=bool(row.get("is_active", 1)),
            provisioned_at=row.get("provisioned_at", "") or "",
            provisioned_by=row.get("provisioned_by", "") or "",
            custom_domain=row.get("custom_domain", "") or "",
            ssl_status=row.get("ssl_status", "pending") or "pending",
            settings=row.get("settings", "{}") or "{}",
            created_at=row.get("created_at", "") or "",
            updated_at=row.get("updated_at", "") or "",
        )

    def to_dict(self, scope="default"):
        d = {
            "org_id": self.org_id,
            "subdomain": self.subdomain,
            "is_active": self.is_active,
            "provisioned_at": self.provisioned_at,
            "custom_domain": self.custom_domain,
            "ssl_status": self.ssl_status,
        }
        if scope == "admin":
            d["provisioned_by"] = self.provisioned_by
            d["settings"] = self.settings
            d["created_at"] = self.created_at
            d["updated_at"] = self.updated_at
        return d


@dataclass
class OrgContext:
    """Resolved org context from subdomain lookup — injected into request scope."""

    org_id: str = ""
    subdomain: str = ""
    plan: str = "free"
    settings: str = "{}"
    is_active: bool = True

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            org_id=row.get("id", "") or row.get("org_id", ""),
            subdomain=row.get("subdomain", "") or "",
            plan=row.get("plan", "free") or "free",
            settings=row.get("settings", "{}") or "{}",
            is_active=bool(row.get("is_active", 1)),
        )

    def to_dict(self, scope="default"):
        return {
            "org_id": self.org_id,
            "subdomain": self.subdomain,
            "plan": self.plan,
            "is_active": self.is_active,
        }
