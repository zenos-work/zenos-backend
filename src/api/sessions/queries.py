SELECT_BY_USER = (
    "SELECT * FROM user_sessions"
    " WHERE user_id = ? AND is_revoked = 0"
    " ORDER BY last_active_at DESC"
    " LIMIT ? OFFSET ?"
)

COUNT_BY_USER = (
    "SELECT COUNT(*) AS c FROM user_sessions WHERE user_id = ? AND is_revoked = 0"
)

SELECT_BY_ID = "SELECT * FROM user_sessions WHERE id = ? AND user_id = ?"

INSERT_SESSION = (
    "INSERT INTO user_sessions"
    " (id, user_id, device_info, ip_hash, country_code, login_method, expires_at)"
    " VALUES (?, ?, NULLIF(?, ''), NULLIF(?, ''), NULLIF(?, ''), ?, NULLIF(?, ''))"
)

REVOKE_SESSION = (
    "UPDATE user_sessions"
    " SET is_revoked = 1, revoked_at = datetime('now'), revoked_reason = ?"
    " WHERE id = ? AND user_id = ? AND is_revoked = 0"
)

REVOKE_ALL_SESSIONS = (
    "UPDATE user_sessions"
    " SET is_revoked = 1, revoked_at = datetime('now'), revoked_reason = 'bulk_revoke'"
    " WHERE user_id = ? AND is_revoked = 0 AND id != ?"
)

TOUCH_SESSION = "UPDATE user_sessions SET last_active_at = datetime('now') WHERE id = ?"

CLEANUP_EXPIRED = (
    "UPDATE user_sessions"
    " SET is_revoked = 1, revoked_at = datetime('now'), revoked_reason = 'expired'"
    " WHERE is_revoked = 0 AND expires_at IS NOT NULL AND expires_at < datetime('now')"
)
