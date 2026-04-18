"""Phase 11 Step 41 — Subdomain provisioning service."""

import re

from api.subdomains.repository import SubdomainRepository

_SUBDOMAIN_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{1,61}[a-z0-9]$")
_RESERVED = frozenset(
    {
        "www",
        "api",
        "app",
        "admin",
        "mail",
        "ftp",
        "static",
        "cdn",
        "staging",
        "dev",
        "test",
        "localhost",
    }
)


class SubdomainService:
    def __init__(self, env, ctx=None):
        self._repo = SubdomainRepository(env.DB, ctx)

    # ── Validation ───────────────────────────────────────────
    def _validate_subdomain(self, subdomain: str):
        if not subdomain or not _SUBDOMAIN_RE.match(subdomain):
            raise ValueError(
                "Subdomain must be 3-63 chars, lowercase alphanumeric/hyphens, "
                "start and end with alphanumeric"
            )
        if subdomain in _RESERVED:
            raise ValueError(f"Subdomain '{subdomain}' is reserved")

    # ── CRUD ─────────────────────────────────────────────────
    async def provision(self, org_id, subdomain, provisioned_by, custom_domain=""):
        self._validate_subdomain(subdomain)
        existing = await self._repo.get_by_subdomain(subdomain)
        if existing:
            raise ValueError(f"Subdomain '{subdomain}' is already taken")
        await self._repo.create(org_id, subdomain, provisioned_by, custom_domain)
        return {"org_id": org_id, "subdomain": subdomain, "status": "provisioned"}

    async def update(self, org_id, new_subdomain):
        self._validate_subdomain(new_subdomain)
        existing = await self._repo.get_by_subdomain(new_subdomain)
        if existing and existing.org_id != org_id:
            raise ValueError(f"Subdomain '{new_subdomain}' is already taken")
        await self._repo.update_subdomain(org_id, new_subdomain)
        return {"org_id": org_id, "subdomain": new_subdomain, "status": "updated"}

    async def get_by_org(self, org_id):
        cfg = await self._repo.get_by_org(org_id)
        return cfg.to_dict(scope="admin") if cfg else None

    async def list_all(self, limit=50, offset=0):
        items = await self._repo.list_all(limit, offset)
        return [s.to_dict(scope="admin") for s in items]

    async def deactivate(self, org_id):
        await self._repo.deactivate(org_id)
        return {"org_id": org_id, "status": "deactivated"}

    async def delete(self, org_id):
        await self._repo.delete(org_id)
        return {"org_id": org_id, "status": "deleted"}

    # ── Tenant routing ───────────────────────────────────────
    async def resolve_org(self, subdomain):
        ctx = await self._repo.resolve_org(subdomain)
        if not ctx:
            return None
        return ctx.to_dict()

    async def org_info(self, subdomain):
        info = await self._repo.org_info(subdomain)
        if not info:
            return None
        return dict(info) if not isinstance(info, dict) else info
