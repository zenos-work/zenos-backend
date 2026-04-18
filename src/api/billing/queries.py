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

FIND_USER_BY_ID = "SELECT id FROM users WHERE id = ?"
FIND_USER_BY_EMAIL = "SELECT id FROM users WHERE lower(email) = lower(?)"
FIND_USER_BY_STRIPE_CUSTOMER = "SELECT id FROM users WHERE stripe_customer_id = ?"

ACTIVATE_USER_MEMBERSHIP = (
    "UPDATE users SET membership_tier = ?, membership_status = 'active',"
    " subscription_started_at = datetime('now'),"
    " subscription_expires_at = datetime('now', '+30 days'),"
    " stripe_customer_id = COALESCE(?, stripe_customer_id),"
    " stripe_subscription_id = COALESCE(?, stripe_subscription_id)"
    " WHERE id = ?"
)

UPSERT_USER_MEMBERSHIP_BY_SUBSCRIPTION = (
    "INSERT INTO user_memberships"
    " (id, user_id, membership_tier, status, started_at, expires_at, stripe_subscription_id, auto_renew, created_at, updated_at)"
    " VALUES (?, ?, ?, 'active', datetime('now'), datetime('now', '+30 days'), ?, 1, datetime('now'), datetime('now'))"
)

UPDATE_USER_MEMBERSHIP_STATUS_BY_SUBSCRIPTION = (
    "UPDATE user_memberships"
    " SET status = ?, expires_at = CASE WHEN ? = 'cancelled' THEN datetime('now') ELSE expires_at END,"
    "     updated_at = datetime('now')"
    " WHERE stripe_subscription_id = ?"
)

CANCEL_USER_MEMBERSHIP = (
    "UPDATE users SET membership_status = 'cancelled',"
    " subscription_expires_at = datetime('now')"
    " WHERE stripe_subscription_id = ?"
)
