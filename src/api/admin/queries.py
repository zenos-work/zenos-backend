COUNT_ACTIVE_USERS = "SELECT COUNT(*) AS c FROM users WHERE is_active = 1"

COUNT_ARTICLES_BY_STATUS = "SELECT status, COUNT(*) AS c FROM articles GROUP BY status"

COUNT_ACTIVE_COMMENTS = "SELECT COUNT(*) AS c FROM comments WHERE is_deleted = 0"

SELECT_TOP_ARTICLES = (
    "SELECT id, title, views_count, likes_count"
    " FROM articles WHERE status = ?"
    " ORDER BY views_count DESC LIMIT 10"
)

SELECT_APPROVAL_QUEUE = (
    "SELECT a.*, u.name AS author_name"
    " FROM articles a JOIN users u ON a.author_id = u.id"
    " WHERE a.status = ?"
    " ORDER BY a.updated_at ASC"
)

SELECT_ALL_USERS_ADMIN = (
    "SELECT id, email, name, role, is_active, created_at"
    " FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?"
)

SELECT_NOTIFICATIONS_BY_USER = (
    "SELECT * FROM notifications"
    " WHERE user_id = ?"
    " ORDER BY created_at DESC LIMIT ? OFFSET ?"
)

INSERT_NOTIFICATION = (
    "INSERT INTO notifications"
    " (id, user_id, actor_id, type, article_id, comment_id, message)"
    " VALUES (?, ?, ?, ?, ?, ?, ?)"
)

UPDATE_MARK_NOTIFICATIONS_READ = (
    "UPDATE notifications SET is_read = 1" " WHERE user_id = ? AND is_read = 0"
)
