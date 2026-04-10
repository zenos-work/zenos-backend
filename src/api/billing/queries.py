"""Phase 12 Step 47 — Billing and webhook queries."""

INSERT_STRIPE_EVENT = (
    "INSERT INTO stripe_webhook_events"
    " (id, event_id, event_type, payload, signature, status)"
    " VALUES (?, ?, ?, ?, ?, ?)"
)

UPDATE_STRIPE_EVENT_STATUS = (
    "UPDATE stripe_webhook_events SET status = ?, processed_at = datetime('now')"
    " WHERE event_id = ?"
)

SELECT_RECON_BY_PERIOD = (
    "SELECT * FROM billing_discrepancies"
    " WHERE period = ?"
    " ORDER BY severity DESC, created_at DESC"
)

INSERT_DISCREPANCY = (
    "INSERT INTO billing_discrepancies"
    " (id, period, source, reference_id, issue_type, expected_amount_cents, actual_amount_cents, severity, notes)"
    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
)

COUNT_DISCREPANCIES_BY_PERIOD = (
    "SELECT COUNT(*) AS c FROM billing_discrepancies WHERE period = ?"
)
