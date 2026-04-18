# ── Org Add-Ons ────────────────────────────────────────────────────────────
INSERT_ADD_ON = (
    "INSERT INTO org_add_ons"
    " (id, org_id, add_on_type, tier, is_active, enabled_by, limits)"
    " VALUES (?, ?, ?, ?, 1, ?, ?)"
)

SELECT_ADD_ONS_BY_ORG = (
    "SELECT * FROM org_add_ons WHERE org_id = ? ORDER BY created_at DESC"
)

SELECT_ADD_ON_BY_ORG_TYPE = (
    "SELECT * FROM org_add_ons WHERE org_id = ? AND add_on_type = ?"
)

UPDATE_ADD_ON = (
    "UPDATE org_add_ons"
    " SET tier = ?, limits = ?, updated_at = datetime('now')"
    " WHERE org_id = ? AND add_on_type = ?"
)

DISABLE_ADD_ON = (
    "UPDATE org_add_ons"
    " SET is_active = 0, updated_at = datetime('now')"
    " WHERE org_id = ? AND add_on_type = ?"
)

COUNT_ADD_ONS_SUMMARY = (
    "SELECT add_on_type, COUNT(*) AS c"
    " FROM org_add_ons WHERE is_active = 1"
    " GROUP BY add_on_type"
)
