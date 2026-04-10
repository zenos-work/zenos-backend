"""Phase 11 Step 42 — SSO service (SAML + OIDC)."""

from api.sso.repository import SsoRepository
from models.sso.model import SsoConfig
from utils.helpers import new_id


class SsoService:
    def __init__(self, env, ctx=None):
        self._repo = SsoRepository(env.DB, ctx)
        self._env = env

    # ── Config CRUD ──────────────────────────────────────────
    async def list_configs(self, org_id):
        items = await self._repo.list_configs(org_id)
        return [c.to_dict(scope="admin") for c in items]

    async def get_config(self, config_id):
        c = await self._repo.get_config(config_id)
        return c.to_dict(scope="admin") if c else None

    async def create_config(self, org_id, data: dict):
        cfg = SsoConfig(
            id=new_id(),
            org_id=org_id,
            provider_type=data.get("provider_type", ""),
            protocol=data.get("protocol", "oidc"),
            client_id=data.get("client_id", ""),
            client_secret=data.get("client_secret", ""),
            issuer_url=data.get("issuer_url", ""),
            metadata_url=data.get("metadata_url", ""),
            entity_id=data.get("entity_id", ""),
            acs_url=data.get("acs_url", ""),
            slo_url=data.get("slo_url", ""),
            certificate=data.get("certificate", ""),
            is_active=data.get("is_active", True),
            enforce_sso=data.get("enforce_sso", False),
            jit_provisioning=data.get("jit_provisioning", True),
            default_role=data.get("default_role", "READER"),
            allowed_domains=data.get("allowed_domains", ""),
        )
        if not cfg.provider_type:
            raise ValueError("provider_type is required")
        if not cfg.issuer_url and cfg.protocol == "oidc":
            raise ValueError("issuer_url is required for OIDC")
        await self._repo.create_config(cfg)
        return cfg.to_dict(scope="admin")

    async def update_config(self, config_id, data: dict):
        existing = await self._repo.get_config(config_id)
        if not existing:
            raise ValueError("SSO config not found")
        for k, v in data.items():
            if hasattr(existing, k):
                setattr(existing, k, v)
        await self._repo.update_config(existing)
        return existing.to_dict(scope="admin")

    async def delete_config(self, config_id):
        await self._repo.delete_config(config_id)
        return {"id": config_id, "deleted": True}

    # ── OIDC Flow ────────────────────────────────────────────
    async def oidc_authorize_url(self, org_id, redirect_url=""):
        cfg = await self._repo.get_active_config(org_id)
        if not cfg or cfg.protocol != "oidc":
            raise ValueError("No active OIDC config for this organization")
        state = new_id()
        nonce = new_id()
        sid = new_id()
        await self._repo.create_session(sid, org_id, state, nonce, redirect_url)
        authorize_url = (
            f"{cfg.issuer_url}/authorize?"
            f"client_id={cfg.client_id}&"
            f"response_type=code&"
            f"scope=openid+email+profile&"
            f"state={state}&"
            f"nonce={nonce}&"
            f"redirect_uri={cfg.acs_url}"
        )
        return {"authorize_url": authorize_url, "state": state}

    async def oidc_callback(self, org_id, state, code):
        session = await self._repo.get_session_by_state(state)
        if not session:
            raise ValueError("Invalid or expired SSO state")
        if session.org_id != org_id:
            raise ValueError("Organization mismatch")
        await self._repo.delete_session(session.id)
        # In production: exchange code for tokens via fetch() to IdP
        # For now: return success with code acknowledgement
        return {
            "org_id": org_id,
            "status": "authenticated",
            "code_received": bool(code),
            "redirect_url": session.redirect_url,
        }

    # ── SAML Flow ────────────────────────────────────────────
    async def saml_metadata(self, org_id):
        cfg = await self._repo.get_active_config(org_id)
        if not cfg or cfg.protocol != "saml":
            raise ValueError("No active SAML config for this organization")
        sp_entity_id = cfg.entity_id or f"https://zenos.work/saml/{org_id}"
        sp_acs_url = cfg.acs_url or f"https://zenos.work/api/auth/sso/saml/{org_id}/acs"
        metadata = (
            f'<?xml version="1.0"?>'
            f'<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata" '
            f'entityID="{sp_entity_id}">'
            f"<SPSSODescriptor>"
            f'<AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST" '
            f'Location="{sp_acs_url}" index="0"/>'
            f"</SPSSODescriptor>"
            f"</EntityDescriptor>"
        )
        return metadata

    async def saml_login_url(self, org_id):
        cfg = await self._repo.get_active_config(org_id)
        if not cfg or cfg.protocol != "saml":
            raise ValueError("No active SAML config for this organization")
        state = new_id()
        sid = new_id()
        await self._repo.create_session(sid, org_id, state, "", "")
        login_url = f"{cfg.issuer_url}?SAMLRequest=encoded&RelayState={state}"
        return {"login_url": login_url, "state": state}

    async def saml_acs(self, org_id, saml_response, relay_state):
        session = await self._repo.get_session_by_state(relay_state)
        if not session:
            raise ValueError("Invalid or expired SAML relay state")
        await self._repo.delete_session(session.id)
        # In production: parse + validate SAML assertion XML
        return {
            "org_id": org_id,
            "status": "authenticated",
            "assertion_received": bool(saml_response),
        }
