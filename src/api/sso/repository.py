"""Phase 11 Step 42 — SSO repository."""

from db.repository import BaseRepository
from api.sso import queries as Q
from models.sso.model import SsoConfig, SsoSession


class SsoRepository(BaseRepository):
    def _one(self, cls, row):
        return self.map_one(row, cls)

    def _many(self, rows, cls):
        return self.map_many(rows, cls)

    # ── SSO Config ───────────────────────────────────────────
    async def get_config(self, config_id):
        return self._one(SsoConfig, await self.find_one(Q.GET_SSO_CONFIG, config_id))

    async def get_active_config(self, org_id):
        return self._one(
            SsoConfig, await self.find_one(Q.GET_SSO_CONFIG_BY_ORG, org_id)
        )

    async def list_configs(self, org_id):
        return self._many(await self.find_all(Q.LIST_SSO_CONFIGS, org_id), SsoConfig)

    async def create_config(self, cfg: SsoConfig):
        await self.execute(
            Q.INSERT_SSO_CONFIG,
            cfg.id,
            cfg.org_id,
            cfg.provider_type,
            cfg.protocol,
            cfg.client_id,
            cfg.client_secret,
            cfg.issuer_url,
            cfg.metadata_url,
            cfg.entity_id,
            cfg.acs_url,
            cfg.slo_url,
            cfg.certificate,
            int(cfg.is_active),
            int(cfg.enforce_sso),
            int(cfg.jit_provisioning),
            cfg.default_role,
            cfg.allowed_domains,
        )

    async def update_config(self, cfg: SsoConfig):
        await self.execute(
            Q.UPDATE_SSO_CONFIG,
            cfg.provider_type,
            cfg.protocol,
            cfg.client_id,
            cfg.client_secret,
            cfg.issuer_url,
            cfg.metadata_url,
            cfg.entity_id,
            cfg.acs_url,
            cfg.slo_url,
            cfg.certificate,
            int(cfg.is_active),
            int(cfg.enforce_sso),
            int(cfg.jit_provisioning),
            cfg.default_role,
            cfg.allowed_domains,
            cfg.id,
        )

    async def delete_config(self, config_id):
        await self.execute(Q.DELETE_SSO_CONFIG, config_id)

    async def deactivate_config(self, config_id):
        await self.execute(Q.DEACTIVATE_SSO_CONFIG, config_id)

    # ── SSO Sessions ─────────────────────────────────────────
    async def create_session(self, sid, org_id, state, nonce, redirect_url=""):
        await self.execute(
            Q.INSERT_SSO_SESSION, sid, org_id, state, nonce, redirect_url
        )

    async def get_session_by_state(self, state):
        return self._one(
            SsoSession, await self.find_one(Q.GET_SSO_SESSION_BY_STATE, state)
        )

    async def delete_session(self, sid):
        await self.execute(Q.DELETE_SSO_SESSION, sid)

    async def cleanup_expired(self):
        await self.execute(Q.CLEANUP_EXPIRED_SESSIONS)
