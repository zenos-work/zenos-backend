"""Phase 10 Steps 39-40 — Usage, alerts, and quota queries."""

# ── Alert Rules ──────────────────────────────────────────────
LIST_ALERT_RULES = "SELECT * FROM alert_rules WHERE org_id = ? ORDER BY created_at DESC"
LIST_ACTIVE_ALERTS = "SELECT * FROM alert_rules WHERE org_id = ? AND is_active = 1 ORDER BY created_at DESC"
GET_ALERT_RULE = "SELECT * FROM alert_rules WHERE id = ?"
INSERT_ALERT_RULE = """INSERT INTO alert_rules
    (id, org_id, created_by, name, alert_type, config, threshold_value,
     comparison, notify_channels, notify_user_ids, cooldown_minutes, is_active)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
UPDATE_ALERT_RULE = """UPDATE alert_rules SET
    name=?, alert_type=?, config=?, threshold_value=?, comparison=?,
    notify_channels=?, notify_user_ids=?, cooldown_minutes=?, is_active=?,
    updated_at=datetime('now') WHERE id=?"""
DELETE_ALERT_RULE = "DELETE FROM alert_rules WHERE id = ?"
TOGGLE_ALERT_RULE = (
    "UPDATE alert_rules SET is_active = ?, updated_at=datetime('now') WHERE id = ?"
)
TRIGGER_ALERT = """UPDATE alert_rules SET
    last_triggered_at=datetime('now'), trigger_count=trigger_count+1,
    updated_at=datetime('now') WHERE id=?"""

# ── Quota (reads from add_on_tier_defaults + org_cost_monthly_rollup) ──
GET_ORG_WORKFLOW_LIMIT = """SELECT td.limit_value
    FROM org_add_ons oa
    JOIN add_on_tier_defaults td ON td.add_on_type = oa.add_on_type AND td.tier = oa.tier
    WHERE oa.org_id = ? AND oa.add_on_type = 'workflow_automation' AND td.limit_key = 'workflow_runs_per_month'
    LIMIT 1"""
GET_ORG_MONTHLY_RUNS = """SELECT workflow_runs
    FROM org_cost_monthly_rollup
    WHERE org_id = ? AND year_month = ?"""
