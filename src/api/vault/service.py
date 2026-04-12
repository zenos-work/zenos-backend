"""Phase 11 Step 44 — Credential vault service."""

import json

from api.vault.repository import VaultRepository
from api.vault.providers import VaultProviderRouter
from utils.helpers import new_id


class VaultService:
    def __init__(self, env, ctx=None):
        self._env = env
        self._repo = VaultRepository(env.DB, ctx)
        self._providers = VaultProviderRouter(env, self._repo)

    async def list_secrets(self, org_id):
        items = await self._repo.list_secrets(org_id)
        return [s.to_dict() for s in items]

    async def store_secret(
        self,
        org_id,
        name,
        secret_type,
        created_by,
        metadata="{}",
        provider="cloudflare",
        key_ref="",
        secret_value="",
    ):
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

        resolved_provider = (provider or "cloudflare").strip().lower()
        resolved_key_ref = key_ref or f"org:{org_id}:secret:{name}"
        if secret_value:
            resolved_provider, resolved_key_ref = await self._providers.store(
                secret_id=sid,
                key_ref=resolved_key_ref,
                secret_value=secret_value,
                preferred_provider=resolved_provider,
            )

        safe_metadata = (
            metadata if isinstance(metadata, str) else json.dumps(metadata or {})
        )
        await self._repo.create_secret(
            sid,
            org_id,
            name,
            secret_type,
            resolved_provider,
            resolved_key_ref,
            created_by,
            safe_metadata,
        )
        await self._repo.increment_write_quota(org_id)
        return {
            "id": sid,
            "name": name,
            "secret_type": secret_type,
            "provider": resolved_provider,
            "key_ref": resolved_key_ref,
        }

    async def revoke_secret(self, org_id, secret_id):
        existing = await self._repo.get_secret(secret_id, org_id)
        if not existing:
            raise ValueError("Secret not found")
        await self._providers.delete(
            existing.provider, existing.key_ref or "", existing.id
        )
        await self._repo.deactivate(secret_id)
        return {"id": secret_id, "revoked": True}

    async def rotate_secret(self, org_id, name, secret_value=""):
        existing = await self._repo.get_secret_by_name(org_id, name)
        if not existing:
            raise ValueError(f"Secret '{name}' not found")
        # Check write quota
        quota = await self._repo.get_write_quota(org_id)
        if quota and quota.write_count >= quota.max_writes:
            raise PermissionError("Daily vault write limit reached")

        provider = existing.provider
        key_ref = existing.key_ref
        if secret_value:
            provider, key_ref = await self._providers.store(
                secret_id=existing.id,
                key_ref=existing.key_ref or f"org:{org_id}:secret:{name}",
                secret_value=secret_value,
                preferred_provider=existing.provider or "cloudflare",
            )
            await self._repo.update_secret_provider_ref(existing.id, provider, key_ref)

        await self._repo.mark_rotated(existing.id)
        await self._repo.increment_write_quota(org_id)
        return {
            "id": existing.id,
            "name": name,
            "rotated": True,
            "provider": provider,
            "key_ref": key_ref,
        }

    async def test_secret(self, org_id, name):
        existing = await self._repo.get_secret_by_name(org_id, name)
        if not existing:
            raise ValueError(f"Secret '{name}' not found")
        resolved = await self._providers.resolve(
            existing.provider,
            existing.key_ref or "",
            existing.id,
        )
        return {
            "name": name,
            "provider": existing.provider,
            "exists": bool(existing.id),
            "is_active": existing.is_active,
            "resolvable": bool(resolved),
        }

    async def resolve_secret(self, org_id, name):
        existing = await self._repo.get_secret_by_name(org_id, name)
        if not existing:
            raise ValueError(f"Secret '{name}' not found")
        value = await self._providers.resolve(
            existing.provider,
            existing.key_ref or "",
            existing.id,
        )
        if not value:
            raise ValueError("Secret value is unavailable from configured provider")
        return {
            "name": name,
            "provider": existing.provider,
            "key_ref": existing.key_ref,
            "value": value,
        }

    async def delete_secret(self, org_id, secret_id):
        existing = await self._repo.get_secret(secret_id, org_id)
        if not existing:
            raise ValueError("Secret not found")
        await self._repo.delete(secret_id)
        return {"id": secret_id, "deleted": True}
