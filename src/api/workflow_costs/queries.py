"""Phase 10 Step 37 — Workflow cost queries."""

# ── Cost Rates ───────────────────────────────────────────────
LIST_RATES = (
    "SELECT * FROM workflow_node_cost_rates WHERE org_id = ? ORDER BY node_type_id"
)
LIST_GLOBAL_RATES = (
    "SELECT * FROM workflow_node_cost_rates WHERE org_id IS NULL ORDER BY node_type_id"
)
GET_RATE = "SELECT * FROM workflow_node_cost_rates WHERE id = ?"
GET_RATE_FOR_NODE = (
    "SELECT * FROM workflow_node_cost_rates WHERE org_id = ? AND node_type_id = ?"
)
INSERT_RATE = """INSERT INTO workflow_node_cost_rates
    (id, org_id, node_type_id, cost_model, rate_microcents, unit_label, currency, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
UPDATE_RATE = """UPDATE workflow_node_cost_rates SET
    cost_model=?, rate_microcents=?, unit_label=?, currency=?, notes=?
    WHERE id=?"""
DELETE_RATE = "DELETE FROM workflow_node_cost_rates WHERE id = ?"

# ── Run Costs ────────────────────────────────────────────────
LIST_RUN_COSTS = (
    "SELECT * FROM workflow_run_costs WHERE run_id = ? ORDER BY created_at DESC"
)
LIST_WORKFLOW_COSTS = "SELECT * FROM workflow_run_costs WHERE workflow_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
GET_RUN_COST = "SELECT * FROM workflow_run_costs WHERE id = ?"
INSERT_RUN_COST = """INSERT INTO workflow_run_costs
    (id, run_id, step_id, workflow_id, org_id, node_type_id,
     cost_model, units_consumed, unit_label, cost_microcents,
     cost_actual_microcents, currency, external_ref, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

# ── Cost Summary ─────────────────────────────────────────────
GET_COST_SUMMARY = "SELECT * FROM workflow_cost_summary WHERE workflow_id = ?"
LIST_COST_SUMMARIES = "SELECT * FROM workflow_cost_summary WHERE org_id = ? ORDER BY total_cost_microcents DESC"
UPSERT_COST_SUMMARY = """INSERT INTO workflow_cost_summary
    (workflow_id, org_id, total_runs_costed, total_cost_microcents,
     total_ad_spend_microcents, total_ai_cost_microcents,
     total_email_cost_microcents, last_run_cost_microcents,
     avg_run_cost_microcents, currency)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(workflow_id) DO UPDATE SET
     total_runs_costed=excluded.total_runs_costed,
     total_cost_microcents=excluded.total_cost_microcents,
     total_ad_spend_microcents=excluded.total_ad_spend_microcents,
     total_ai_cost_microcents=excluded.total_ai_cost_microcents,
     total_email_cost_microcents=excluded.total_email_cost_microcents,
     last_run_cost_microcents=excluded.last_run_cost_microcents,
     avg_run_cost_microcents=excluded.avg_run_cost_microcents,
     updated_at=datetime('now')"""

# ── Monthly Rollup ───────────────────────────────────────────
GET_MONTHLY_ROLLUP = (
    "SELECT * FROM org_cost_monthly_rollup WHERE org_id = ? AND year_month = ?"
)
LIST_MONTHLY_ROLLUPS = "SELECT * FROM org_cost_monthly_rollup WHERE org_id = ? ORDER BY year_month DESC LIMIT ? OFFSET ?"
UPSERT_MONTHLY_ROLLUP = """INSERT INTO org_cost_monthly_rollup
    (id, org_id, year_month, workflow_runs, total_cost_microcents,
     ad_spend_microcents, ai_cost_microcents, email_cost_microcents,
     other_cost_microcents, budget_cap_microcents)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(org_id, year_month) DO UPDATE SET
     workflow_runs=excluded.workflow_runs,
     total_cost_microcents=excluded.total_cost_microcents,
     ad_spend_microcents=excluded.ad_spend_microcents,
     ai_cost_microcents=excluded.ai_cost_microcents,
     email_cost_microcents=excluded.email_cost_microcents,
     other_cost_microcents=excluded.other_cost_microcents,
     budget_cap_microcents=excluded.budget_cap_microcents,
     updated_at=datetime('now')"""
SET_BUDGET_CAP = "UPDATE org_cost_monthly_rollup SET budget_cap_microcents = ?, updated_at=datetime('now') WHERE org_id = ? AND year_month = ?"
