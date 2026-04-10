"""Phase 11 Step 44 — Credential vault queries."""

# ── Vault secret metadata (stored in D1) ─────────────────────
LIST_SECRETS = (
    "SELECT * FROM vault_secrets WHERE org_id = ? AND is_active = 1 ORDER BY name"
)
GET_SECRET = "SELECT * FROM vault_secrets WHERE id = ? AND org_id = ?"
GET_SECRET_BY_NAME = "SELECT * FROM vault_secrets WHERE org_id = ? AND name = ?"

INSERT_SECRET = """INSERT INTO vault_secrets
    (id, org_id, name, secret_type, is_active, created_by, metadata)
    VALUES (?, ?, ?, ?, 1, ?, ?)"""

UPDATE_SECRET_ROTATED = """UPDATE vault_secrets
    SET last_rotated_at = datetime('now'), updated_at = datetime('now')
    WHERE id = ?"""

DEACTIVATE_SECRET = """UPDATE vault_secrets
    SET is_active = 0, updated_at = datetime('now')
    WHERE id = ?"""

DELETE_SECRET = "DELETE FROM vault_secrets WHERE id = ?"

# ── Write quota tracking ─────────────────────────────────────
GET_WRITE_QUOTA = (
    "SELECT * FROM vault_write_quotas WHERE org_id = ? AND date = date('now')"
)

UPSERT_WRITE_QUOTA = """INSERT INTO vault_write_quotas (org_id, date, write_count, max_writes)
    VALUES (?, date('now'), 1, 50)
    ON CONFLICT(org_id, date) DO UPDATE SET write_count = write_count + 1"""
