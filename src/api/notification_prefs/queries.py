"""Phase 10 Step 36 — Notification preference queries."""

# ── Preferences ──────────────────────────────────────────────
LIST_PREFS = "SELECT * FROM notification_preferences WHERE user_id = ?"
GET_PREF = "SELECT * FROM notification_preferences WHERE user_id = ? AND notification_type = ? AND channel = ?"
UPSERT_PREF = """INSERT INTO notification_preferences (user_id, notification_type, channel, is_enabled)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(user_id, notification_type, channel) DO UPDATE SET is_enabled=excluded.is_enabled"""
DELETE_PREF = "DELETE FROM notification_preferences WHERE user_id = ? AND notification_type = ? AND channel = ?"

# ── Push Subscriptions ──────────────────────────────────────
LIST_PUSH_SUBS = "SELECT * FROM push_subscriptions WHERE user_id = ? AND is_active = 1"
GET_PUSH_SUB = "SELECT * FROM push_subscriptions WHERE id = ?"
GET_PUSH_SUB_BY_ENDPOINT = (
    "SELECT * FROM push_subscriptions WHERE user_id = ? AND endpoint = ?"
)
INSERT_PUSH_SUB = """INSERT INTO push_subscriptions
    (id, user_id, platform, endpoint, p256dh_key, auth_key, device_name)
    VALUES (?, ?, ?, ?, ?, ?, ?)"""
DEACTIVATE_PUSH_SUB = "UPDATE push_subscriptions SET is_active = 0 WHERE id = ?"
DELETE_PUSH_SUB = "DELETE FROM push_subscriptions WHERE id = ?"
