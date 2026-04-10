"""Phase 11 Step 42 — SSO models."""

from dataclasses import dataclass


@dataclass
class SsoConfig:
    id: str = ""
    org_id: str = ""
    provider_type: str = ""  # azure_ad, okta, google_workspace
    protocol: str = ""  # saml, oidc
    client_id: str = ""
    client_secret: str = ""
    issuer_url: str = ""
    metadata_url: str = ""
    entity_id: str = ""
    acs_url: str = ""
    slo_url: str = ""
    certificate: str = ""
    is_active: bool = True
    enforce_sso: bool = False
    jit_provisioning: bool = True
    default_role: str = "READER"
    allowed_domains: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id", ""),
            provider_type=row.get("provider_type", ""),
            protocol=row.get("protocol", ""),
            client_id=row.get("client_id", "") or "",
            client_secret=row.get("client_secret", "") or "",
            issuer_url=row.get("issuer_url", "") or "",
            metadata_url=row.get("metadata_url", "") or "",
            entity_id=row.get("entity_id", "") or "",
            acs_url=row.get("acs_url", "") or "",
            slo_url=row.get("slo_url", "") or "",
            certificate=row.get("certificate", "") or "",
            is_active=bool(row.get("is_active", 1)),
            enforce_sso=bool(row.get("enforce_sso", 0)),
            jit_provisioning=bool(row.get("jit_provisioning", 1)),
            default_role=row.get("default_role", "READER") or "READER",
            allowed_domains=row.get("allowed_domains", "") or "",
            created_at=row.get("created_at", "") or "",
            updated_at=row.get("updated_at", "") or "",
        )

    def to_dict(self, scope="default"):
        d = {
            "id": self.id,
            "org_id": self.org_id,
            "provider_type": self.provider_type,
            "protocol": self.protocol,
            "issuer_url": self.issuer_url,
            "is_active": self.is_active,
            "enforce_sso": self.enforce_sso,
            "jit_provisioning": self.jit_provisioning,
            "default_role": self.default_role,
        }
        if scope == "admin":
            d["client_id"] = self.client_id
            d["metadata_url"] = self.metadata_url
            d["entity_id"] = self.entity_id
            d["acs_url"] = self.acs_url
            d["slo_url"] = self.slo_url
            d["allowed_domains"] = self.allowed_domains
            d["created_at"] = self.created_at
            d["updated_at"] = self.updated_at
        return d


@dataclass
class SsoSession:
    """Tracks an SSO login attempt for CSRF/replay protection."""

    id: str = ""
    org_id: str = ""
    state: str = ""
    nonce: str = ""
    redirect_url: str = ""
    created_at: str = ""
    expires_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id", ""),
            state=row.get("state", ""),
            nonce=row.get("nonce", ""),
            redirect_url=row.get("redirect_url", "") or "",
            created_at=row.get("created_at", "") or "",
            expires_at=row.get("expires_at", "") or "",
        )

    def to_dict(self, scope="default"):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "state": self.state,
        }
