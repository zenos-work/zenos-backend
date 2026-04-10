"""Phase 11 Step 44 — Credential vault repository."""

from db.repository import BaseRepository
from api.vault import queries as Q
from models.vault.model import VaultSecret, VaultWriteQuota


class VaultRepository(BaseRepository):
    def _one(self, cls, row):
        return self.map_one(row, cls)

    def _many(self, rows, cls):
        return self.map_many(rows, cls)

    # ── Secrets metadata ─────────────────────────────────────
    async def list_secrets(self, org_id):
        return self._many(await self.find_all(Q.LIST_SECRETS, org_id), VaultSecret)

    async def get_secret(self, secret_id, org_id):
        return self._one(
            VaultSecret, await self.find_one(Q.GET_SECRET, secret_id, org_id)
        )

    async def get_secret_by_name(self, org_id, name):
        return self._one(
            VaultSecret, await self.find_one(Q.GET_SECRET_BY_NAME, org_id, name)
        )

    async def create_secret(
        self, sid, org_id, name, secret_type, created_by, metadata="{}"
    ):
        await self.execute(
            Q.INSERT_SECRET, sid, org_id, name, secret_type, created_by, metadata
        )

    async def mark_rotated(self, secret_id):
        await self.execute(Q.UPDATE_SECRET_ROTATED, secret_id)

    async def deactivate(self, secret_id):
        await self.execute(Q.DEACTIVATE_SECRET, secret_id)

    async def delete(self, secret_id):
        await self.execute(Q.DELETE_SECRET, secret_id)

    # ── Write quota ──────────────────────────────────────────
    async def get_write_quota(self, org_id):
        return self._one(
            VaultWriteQuota, await self.find_one(Q.GET_WRITE_QUOTA, org_id)
        )

    async def increment_write_quota(self, org_id):
        await self.execute(Q.UPSERT_WRITE_QUOTA, org_id)
