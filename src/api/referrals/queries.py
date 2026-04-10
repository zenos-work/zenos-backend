"""Phase 9 Step 34 — Referral queries."""

# ── Codes ────────────────────────────────────────────────────
GET_CODE_BY_USER = "SELECT * FROM referral_codes WHERE user_id = ?"
GET_CODE_BY_CODE = "SELECT * FROM referral_codes WHERE code = ?"
GET_CODE = "SELECT * FROM referral_codes WHERE id = ?"
INSERT_CODE = "INSERT INTO referral_codes (id, user_id, code) VALUES (?, ?, ?)"
INCREMENT_CLICKS = (
    "UPDATE referral_codes SET total_clicks = total_clicks + 1 WHERE id = ?"
)
INCREMENT_SIGNUPS = (
    "UPDATE referral_codes SET total_signups = total_signups + 1 WHERE id = ?"
)
INCREMENT_CONVERSIONS = "UPDATE referral_codes SET total_conversions = total_conversions + 1, reward_credits = reward_credits + 1 WHERE id = ?"

# ── Events ───────────────────────────────────────────────────
LIST_EVENTS = "SELECT * FROM referral_events WHERE referral_code_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
INSERT_EVENT = "INSERT INTO referral_events (id, referral_code_id, event_type, referred_user_id, metadata) VALUES (?, ?, ?, ?, ?)"
