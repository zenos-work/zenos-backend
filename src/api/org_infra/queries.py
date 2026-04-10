# ── Audit Log ──────────────────────────────────────────────────────────────
INSERT_AUDIT = (
    "INSERT INTO audit_log"
    " (id, org_id, actor_id, actor_ip, action, resource, resource_id, payload)"
    " VALUES (?, ?, NULLIF(?, ''), NULLIF(?, ''), ?, NULLIF(?, ''), NULLIF(?, ''), ?)"
)

SELECT_AUDIT_BY_ORG = (
    "SELECT * FROM audit_log WHERE org_id = ?"
    " ORDER BY created_at DESC"
    " LIMIT ? OFFSET ?"
)

COUNT_AUDIT_BY_ORG = "SELECT COUNT(*) AS c FROM audit_log WHERE org_id = ?"

# ── API Keys ──────────────────────────────────────────────────────────────
INSERT_API_KEY = (
    "INSERT INTO api_keys"
    " (id, org_id, name, key_hash, key_prefix, scopes, created_by)"
    " VALUES (?, ?, ?, ?, ?, ?, ?)"
)

SELECT_API_KEYS_BY_ORG = (
    "SELECT * FROM api_keys WHERE org_id = ? AND revoked_at IS NULL"
    " ORDER BY created_at DESC"
    " LIMIT ? OFFSET ?"
)

COUNT_API_KEYS_BY_ORG = (
    "SELECT COUNT(*) AS c FROM api_keys WHERE org_id = ? AND revoked_at IS NULL"
)

REVOKE_API_KEY = (
    "UPDATE api_keys SET revoked_at = datetime('now') WHERE id = ? AND org_id = ?"
)

# ── SSO Configs ───────────────────────────────────────────────────────────
INSERT_SSO = (
    "INSERT INTO sso_configs"
    " (id, org_id, provider, metadata, is_enabled, created_by)"
    " VALUES (?, ?, ?, ?, ?, ?)"
)

SELECT_SSO_BY_ORG = "SELECT * FROM sso_configs WHERE org_id = ?"

UPDATE_SSO = (
    "UPDATE sso_configs"
    " SET provider = ?, metadata = ?, is_enabled = ?, updated_at = datetime('now')"
    " WHERE org_id = ?"
)
