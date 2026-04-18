from typing import Optional, List
from db.repository import BaseRepository
from api.org_infra import queries as Q
from models.org_infra.model import AuditLogEntry, ApiKey, SsoConfig
from models.base import row_get


class OrgInfraRepository(BaseRepository):
    # ── Audit Log ──────────────────────────────────────────────────────
    async def insert_audit(
        self,
        audit_id,
        org_id,
        actor_id,
        actor_ip,
        action,
        resource,
        resource_id,
        payload="{}",
    ):
        await self.execute(
            Q.INSERT_AUDIT,
            audit_id,
            org_id,
            actor_id or "",
            actor_ip or "",
            action,
            resource or "",
            resource_id or "",
            payload,
        )

    async def find_audit_by_org(self, org_id, limit, offset) -> List[AuditLogEntry]:
        rows = await self.find_all(Q.SELECT_AUDIT_BY_ORG, org_id, limit, offset)
        return self.map_many(rows, AuditLogEntry)

    async def count_audit_by_org(self, org_id) -> int:
        row = await self.find_one(Q.COUNT_AUDIT_BY_ORG, org_id)
        return row_get(row, "c", 0)

    # ── API Keys ──────────────────────────────────────────────────────
    async def create_api_key(
        self, key_id, org_id, name, key_hash, key_prefix, scopes, created_by
    ):
        await self.execute(
            Q.INSERT_API_KEY,
            key_id,
            org_id,
            name,
            key_hash,
            key_prefix,
            scopes,
            created_by,
        )

    async def find_api_keys(self, org_id, limit, offset) -> List[ApiKey]:
        rows = await self.find_all(Q.SELECT_API_KEYS_BY_ORG, org_id, limit, offset)
        return self.map_many(rows, ApiKey)

    async def count_api_keys(self, org_id) -> int:
        row = await self.find_one(Q.COUNT_API_KEYS_BY_ORG, org_id)
        return row_get(row, "c", 0)

    async def revoke_api_key(self, key_id, org_id):
        await self.execute(Q.REVOKE_API_KEY, key_id, org_id)

    # ── SSO ────────────────────────────────────────────────────────────
    async def create_sso(
        self, sso_id, org_id, provider, metadata, is_enabled, created_by
    ):
        await self.execute(
            Q.INSERT_SSO, sso_id, org_id, provider, metadata, is_enabled, created_by
        )

    async def find_sso_by_org(self, org_id) -> Optional[SsoConfig]:
        row = await self.find_one(Q.SELECT_SSO_BY_ORG, org_id)
        return self.map_one(row, SsoConfig)

    async def update_sso(self, org_id, provider, metadata, is_enabled):
        await self.execute(Q.UPDATE_SSO, provider, metadata, is_enabled, org_id)
