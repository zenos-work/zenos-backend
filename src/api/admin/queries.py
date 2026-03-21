COUNT_ACTIVE_USERS = "SELECT COUNT(*) AS c FROM users WHERE is_active = 1"

COUNT_USERS_TOTAL = "SELECT COUNT(*) AS c FROM users"

COUNT_USERS_BY_ROLE = "SELECT role, COUNT(*) AS c FROM users GROUP BY role"

COUNT_ARTICLES_BY_STATUS = "SELECT status, COUNT(*) AS c FROM articles GROUP BY status"

COUNT_ACTIVE_COMMENTS = "SELECT COUNT(*) AS c FROM comments WHERE is_deleted = 0"

COUNT_PENDING_APPROVALS = (
    "SELECT COUNT(*) AS c FROM articles WHERE status = 'SUBMITTED'"
)

COUNT_FLAGGED_COMMENTS = (
    "SELECT COUNT(*) AS c FROM comments"
    " WHERE is_deleted = 0 AND is_hidden = 0 AND flag_count > 0"
)

COUNT_HIDDEN_COMMENTS = "SELECT COUNT(*) AS c FROM comments WHERE is_hidden = 1"

COUNT_NOTIFICATIONS_LAST_7D = (
    "SELECT COUNT(*) AS c FROM notifications"
    " WHERE created_at >= datetime('now', '-7 days')"
)

COUNT_PUBLISHED_LAST_7D = (
    "SELECT COUNT(*) AS c FROM articles"
    " WHERE status = 'PUBLISHED'"
    "   AND COALESCE(published_at, updated_at, created_at) >= datetime('now', '-7 days')"
)

COUNT_APPROVED_LAST_7D = (
    "SELECT COUNT(*) AS c FROM articles"
    " WHERE status = 'APPROVED'"
    "   AND updated_at >= datetime('now', '-7 days')"
)

COUNT_REJECTED_LAST_7D = (
    "SELECT COUNT(*) AS c FROM articles"
    " WHERE status = 'REJECTED'"
    "   AND updated_at >= datetime('now', '-7 days')"
)

SELECT_TOP_ARTICLES = (
    "SELECT id, title, views_count, likes_count"
    " FROM articles WHERE status = ?"
    " ORDER BY views_count DESC LIMIT 10"
)

SELECT_APPROVAL_QUEUE = (
    "SELECT a.*, u.name AS author_name"
    " FROM articles a JOIN users u ON a.author_id = u.id"
    " WHERE a.status IN (?, ?)"
    " ORDER BY a.updated_at ASC LIMIT ? OFFSET ?"
)

COUNT_APPROVAL_QUEUE = "SELECT COUNT(*) AS c FROM articles WHERE status IN (?, ?)"

SELECT_ALL_USERS_ADMIN = (
    "SELECT id, email, name, role, is_active, created_at"
    " FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?"
)

SELECT_NOTIFICATIONS_BY_USER = (
    "SELECT * FROM notifications"
    " WHERE user_id = ?"
    " ORDER BY created_at DESC LIMIT ? OFFSET ?"
)

COUNT_NOTIFICATIONS_BY_USER = (
    "SELECT COUNT(*) AS c FROM notifications WHERE user_id = ?"
)

INSERT_NOTIFICATION = (
    "INSERT INTO notifications"
    " (id, user_id, actor_id, type, article_id, comment_id, message)"
    " VALUES (?, ?, ?, ?, ?, ?, ?)"
)

UPDATE_MARK_NOTIFICATIONS_READ = (
    "UPDATE notifications SET is_read = 1" " WHERE user_id = ? AND is_read = 0"
)
