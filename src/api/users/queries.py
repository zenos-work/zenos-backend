SELECT_BY_ID = "SELECT * FROM users WHERE id = ?"

SELECT_PUBLIC_BY_ID = (
    "SELECT id, name, role, avatar_url, created_at FROM users WHERE id = ?"
)

SELECT_ALL_USERS = (
    "SELECT id, email, name, role, is_active, created_at"
    " FROM users ORDER BY created_at DESC"
)

SELECT_ARTICLES_BY_AUTHOR = (
    "SELECT a.*, u.name AS author_name, u.avatar_url AS author_avatar"
    " FROM articles a JOIN users u ON a.author_id = u.id"
    " WHERE a.author_id = ? AND a.status != ?"
    " ORDER BY a.updated_at DESC LIMIT ? OFFSET ?"
)

SELECT_PREFS_BY_USER = "SELECT * FROM user_preferences WHERE user_id = ?"

INSERT_PREFS = "INSERT OR IGNORE INTO user_preferences (user_id) VALUES (?)"

UPDATE_PROFILE = (
    "UPDATE users SET name = ?, avatar_url = ?,"
    ' updated_at = datetime("now") WHERE id = ?'
)

UPDATE_ROLE = "UPDATE users SET role = ?," ' updated_at = datetime("now") WHERE id = ?'

UPDATE_SELF_ROLE = "UPDATE users SET role = ?" " WHERE id = ? AND role = ?"

UPDATE_PREFS = (
    "UPDATE user_preferences SET topics = ?, email_notifs = ?, theme = ?,"
    ' updated_at = datetime("now") WHERE user_id = ?'
)

UPDATE_BAN = "UPDATE users SET is_active = 0 WHERE id = ?"

UPDATE_UNBAN = "UPDATE users SET is_active = 1 WHERE id = ?"

UPDATE_ACCEPT_TERMS = (
    "UPDATE users"
    " SET terms_accepted_at = datetime('now'),"
    "     updated_at = datetime('now')"
    " WHERE id = ? AND terms_accepted_at IS NULL"
)

SELECT_TERMS_STATUS = "SELECT terms_accepted_at FROM users WHERE id = ?"
