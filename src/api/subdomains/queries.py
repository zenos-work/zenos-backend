"""Phase 11 Step 41 — Subdomain provisioning queries."""

# ── Subdomain CRUD ───────────────────────────────────────────
GET_BY_SUBDOMAIN = "SELECT * FROM subdomain_configs WHERE subdomain = ?"
GET_BY_ORG = "SELECT * FROM subdomain_configs WHERE org_id = ?"
LIST_ALL = "SELECT * FROM subdomain_configs ORDER BY created_at DESC LIMIT ? OFFSET ?"

INSERT_SUBDOMAIN = """INSERT INTO subdomain_configs
    (org_id, subdomain, is_active, provisioned_by, custom_domain, ssl_status, settings)
    VALUES (?, ?, 1, ?, ?, 'pending', ?)"""

UPDATE_SUBDOMAIN = """UPDATE subdomain_configs
    SET subdomain = ?, updated_at = datetime('now')
    WHERE org_id = ?"""

DEACTIVATE_SUBDOMAIN = """UPDATE subdomain_configs
    SET is_active = 0, updated_at = datetime('now')
    WHERE org_id = ?"""

ACTIVATE_SUBDOMAIN = """UPDATE subdomain_configs
    SET is_active = 1, updated_at = datetime('now')
    WHERE org_id = ?"""

DELETE_SUBDOMAIN = "DELETE FROM subdomain_configs WHERE org_id = ?"

# ── Org lookup for tenant routing ────────────────────────────
RESOLVE_ORG_BY_SUBDOMAIN = """SELECT id, subdomain, plan, settings, is_active
    FROM organizations WHERE subdomain = ? AND is_active = 1"""

# ── Well-known org info ──────────────────────────────────────
ORG_INFO_BY_SUBDOMAIN = """SELECT id AS org_id, name, subdomain, plan, logo_url
    FROM organizations WHERE subdomain = ?"""
