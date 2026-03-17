SELECT_BASE = (
    "SELECT c.*, u.name AS author_name, u.avatar_url AS author_avatar"
    " FROM comments c JOIN users u ON c.author_id = u.id"
)

SELECT_BY_ID = SELECT_BASE + " WHERE c.id = ?"

SELECT_BY_ARTICLE = (
    SELECT_BASE + " WHERE c.article_id = ? AND c.parent_id IS NULL"
    " ORDER BY c.created_at ASC LIMIT ? OFFSET ?"
)

COUNT_BY_ARTICLE = (
    "SELECT COUNT(*) as count FROM comments"
    " WHERE article_id = ? AND parent_id IS NULL"
)

SELECT_REPLIES_BY_PARENT = (
    SELECT_BASE + " WHERE c.parent_id = ? ORDER BY c.created_at ASC"
)

SELECT_REPLIES_PAGINATED = (
    SELECT_BASE + " WHERE c.parent_id = ? ORDER BY c.created_at ASC LIMIT ? OFFSET ?"
)

COUNT_REPLIES = "SELECT COUNT(*) as count FROM comments WHERE parent_id = ?"

SELECT_FOR_MODERATION = (
    SELECT_BASE + " ORDER BY c.flag_count DESC, c.created_at DESC LIMIT ? OFFSET ?"
)

COUNT_ALL_COMMENTS = "SELECT COUNT(*) as count FROM comments"

SELECT_AUTHOR_BY_ID = "SELECT author_id, is_deleted FROM comments WHERE id = ?"

INSERT_COMMENT = (
    "INSERT INTO comments"
    " (id, article_id, author_id, parent_id, content)"
    " VALUES (?, ?, ?, ?, ?)"
)

UPDATE_COMMENT = (
    "UPDATE comments"
    ' SET content = ?, updated_at = datetime("now")'
    " WHERE id = ? AND is_deleted = 0"
)

SOFT_DELETE = (
    "UPDATE comments"
    ' SET is_deleted = 1, updated_at = datetime("now")'
    " WHERE id = ?"
)

INCREMENT_FLAG_COUNT = "UPDATE comments SET flag_count = flag_count + 1 WHERE id = ?"

SET_MODERATION = (
    "UPDATE comments"
    " SET is_hidden = ?, moderation_reason = ?,"
    '     moderated_by = ?, moderated_at = datetime("now"),'
    '     updated_at = datetime("now")'
    " WHERE id = ?"
)
