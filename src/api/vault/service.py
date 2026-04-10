"""Phase 11 Step 44 — Credential vault service."""

from api.vault.repository import VaultRepository
from utils.helpers import new_id


class VaultService:
    def __init__(self, env, ctx=None):
        self._repo = VaultRepository(env.DB, ctx)

    async def list_secrets(self, org_id):
        items = await self._repo.list_secrets(org_id)
        return [s.to_dict() for s in items]

    async def store_secret(self, org_id, name, secret_type, created_by, metadata="{}"):
        if not name:
            raise ValueError("Secret name is required")
        existing = await self._repo.get_secret_by_name(org_id, name)
        if existing:
            raise ValueError(f"Secret '{name}' already exists for this organization")
        # Check write quota
        quota = await self._repo.get_write_quota(org_id)
        if quota and quota.write_count >= quota.max_writes:
            raise PermissionError(
                f"Daily vault write limit reached ({quota.max_writes}). "
                "Try again tomorrow."
            )
        sid = new_id()
        await self._repo.create_secret(
            sid, org_id, name, secret_type, created_by, metadata
        )
        await self._repo.increment_write_quota(org_id)
        return {"id": sid, "name": name, "secret_type": secret_type}

    async def revoke_secret(self, org_id, secret_id):
        existing = await self._repo.get_secret(secret_id, org_id)
        if not existing:
            raise ValueError("Secret not found")
        await self._repo.deactivate(secret_id)
        return {"id": secret_id, "revoked": True}

    async def rotate_secret(self, org_id, name):
        existing = await self._repo.get_secret_by_name(org_id, name)
        if not existing:
            raise ValueError(f"Secret '{name}' not found")
        # Check write quota
        quota = await self._repo.get_write_quota(org_id)
        if quota and quota.write_count >= quota.max_writes:
            raise PermissionError("Daily vault write limit reached")
        await self._repo.mark_rotated(existing.id)
        await self._repo.increment_write_quota(org_id)
        return {"id": existing.id, "name": name, "rotated": True}

    async def test_secret(self, org_id, name):
        existing = await self._repo.get_secret_by_name(org_id, name)
        if not existing:
            raise ValueError(f"Secret '{name}' not found")
        # In production: attempt to use the secret (e.g. OAuth token refresh)
        return {"name": name, "exists": True, "is_active": existing.is_active}

    async def delete_secret(self, org_id, secret_id):
        existing = await self._repo.get_secret(secret_id, org_id)
        if not existing:
            raise ValueError("Secret not found")
        await self._repo.delete(secret_id)
        return {"id": secret_id, "deleted": True}
