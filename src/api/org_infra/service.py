import hashlib
import secrets
from api.org_infra.repository import OrgInfraRepository
from utils.helpers import new_id, paginate

VALID_SSO_PROVIDERS = ("saml", "oidc", "google_workspace", "microsoft_entra")


class OrgInfraService:
    def __init__(self, env, ctx=None):
        self._repo = OrgInfraRepository(env.DB, ctx)

    # ── Audit Log ──────────────────────────────────────────────────────
    async def log_action(
        self,
        org_id,
        actor_id,
        action,
        resource=None,
        resource_id=None,
        actor_ip=None,
        payload="{}",
    ):
        aid = new_id()
        await self._repo.insert_audit(
            aid, org_id, actor_id, actor_ip, action, resource, resource_id, payload
        )
        return aid

    async def list_audit_log(self, org_id, page=1, limit=20):
        _limit, offset = paginate(page, limit)
        entries = await self._repo.find_audit_by_org(org_id, _limit, offset)
        total = await self._repo.count_audit_by_org(org_id)
        return {
            "audit_log": [e.to_dict(scope="admin") for e in entries],
            "pagination": {
                "page": page,
                "limit": _limit,
                "total": total,
                "pages": (total + _limit - 1) // _limit if _limit else 0,
            },
        }

    # ── API Keys ──────────────────────────────────────────────────────
    async def create_api_key(self, org_id, name, scopes, created_by):
        key_id = new_id()
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:8]
        await self._repo.create_api_key(
            key_id, org_id, name, key_hash, key_prefix, scopes, created_by
        )
        return {"id": key_id, "key": raw_key, "key_prefix": key_prefix, "name": name}

    async def list_api_keys(self, org_id, page=1, limit=20):
        _limit, offset = paginate(page, limit)
        keys = await self._repo.find_api_keys(org_id, _limit, offset)
        total = await self._repo.count_api_keys(org_id)
        return {
            "api_keys": [k.to_dict() for k in keys],
            "pagination": {
                "page": page,
                "limit": _limit,
                "total": total,
                "pages": (total + _limit - 1) // _limit if _limit else 0,
            },
        }

    async def revoke_api_key(self, key_id, org_id):
        await self._repo.revoke_api_key(key_id, org_id)

    # ── SSO ────────────────────────────────────────────────────────────
    async def create_sso(self, org_id, provider, metadata, is_enabled, created_by):
        if provider not in VALID_SSO_PROVIDERS:
            raise ValueError(f"Invalid provider: {provider}")
        existing = await self._repo.find_sso_by_org(org_id)
        if existing:
            raise ValueError("SSO config already exists; use update instead")
        sso_id = new_id()
        await self._repo.create_sso(
            sso_id, org_id, provider, metadata, is_enabled, created_by
        )
        config = await self._repo.find_sso_by_org(org_id)
        return config.to_dict(scope="admin") if config else {"id": sso_id}

    async def update_sso(self, org_id, provider, metadata, is_enabled):
        if provider not in VALID_SSO_PROVIDERS:
            raise ValueError(f"Invalid provider: {provider}")
        existing = await self._repo.find_sso_by_org(org_id)
        if not existing:
            raise ValueError("No SSO config found")
        await self._repo.update_sso(org_id, provider, metadata, is_enabled)
        config = await self._repo.find_sso_by_org(org_id)
        return config.to_dict(scope="admin") if config else {}

    async def get_sso(self, org_id):
        config = await self._repo.find_sso_by_org(org_id)
        if not config:
            raise ValueError("No SSO config found")
        return config.to_dict(scope="admin")
