"""Phase 11 Step 42 — SSO queries."""

# ── SSO Config CRUD ──────────────────────────────────────────
GET_SSO_CONFIG = "SELECT * FROM sso_configs WHERE id = ?"
GET_SSO_CONFIG_BY_ORG = "SELECT * FROM sso_configs WHERE org_id = ? AND is_active = 1"
LIST_SSO_CONFIGS = "SELECT * FROM sso_configs WHERE org_id = ? ORDER BY created_at DESC"

INSERT_SSO_CONFIG = """INSERT INTO sso_configs
    (id, org_id, provider_type, protocol, client_id, client_secret,
     issuer_url, metadata_url, entity_id, acs_url, slo_url, certificate,
     is_active, enforce_sso, jit_provisioning, default_role, allowed_domains)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

UPDATE_SSO_CONFIG = """UPDATE sso_configs SET
    provider_type = ?, protocol = ?, client_id = ?, client_secret = ?,
    issuer_url = ?, metadata_url = ?, entity_id = ?, acs_url = ?, slo_url = ?,
    certificate = ?, is_active = ?, enforce_sso = ?, jit_provisioning = ?,
    default_role = ?, allowed_domains = ?, updated_at = datetime('now')
    WHERE id = ?"""

DELETE_SSO_CONFIG = "DELETE FROM sso_configs WHERE id = ?"
DEACTIVATE_SSO_CONFIG = (
    "UPDATE sso_configs SET is_active = 0, updated_at = datetime('now') WHERE id = ?"
)

# ── SSO Sessions (state tracking) ────────────────────────────
INSERT_SSO_SESSION = """INSERT INTO sso_sessions
    (id, org_id, state, nonce, redirect_url, expires_at)
    VALUES (?, ?, ?, ?, ?, datetime('now', '+10 minutes'))"""

GET_SSO_SESSION_BY_STATE = (
    "SELECT * FROM sso_sessions WHERE state = ? AND expires_at > datetime('now')"
)
DELETE_SSO_SESSION = "DELETE FROM sso_sessions WHERE id = ?"
CLEANUP_EXPIRED_SESSIONS = "DELETE FROM sso_sessions WHERE expires_at < datetime('now')"
