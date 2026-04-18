INSERT_DOMAIN = (
    "INSERT INTO custom_domains"
    " (id, org_id, user_id, domain, resource_type, resource_id,"
    "  verification_method, verification_token)"
    " VALUES (?, NULLIF(?, ''), ?, ?, ?, NULLIF(?, ''), ?, ?)"
)

SELECT_BY_USER = (
    "SELECT * FROM custom_domains"
    " WHERE user_id = ?"
    " ORDER BY created_at DESC"
    " LIMIT ? OFFSET ?"
)

COUNT_BY_USER = "SELECT COUNT(*) AS c FROM custom_domains WHERE user_id = ?"

SELECT_BY_ID = "SELECT * FROM custom_domains WHERE id = ?"

SELECT_BY_DOMAIN = "SELECT * FROM custom_domains WHERE domain = ?"

DELETE_DOMAIN = "DELETE FROM custom_domains WHERE id = ? AND user_id = ?"

UPDATE_VERIFICATION = (
    "UPDATE custom_domains"
    " SET verification_status = ?, verified_at = ?,"
    "     is_active = ?, updated_at = datetime('now')"
    " WHERE id = ?"
)

UPDATE_SSL = (
    "UPDATE custom_domains"
    " SET ssl_status = ?, ssl_issued_at = ?, ssl_expires_at = ?,"
    "     updated_at = datetime('now')"
    " WHERE id = ?"
)
