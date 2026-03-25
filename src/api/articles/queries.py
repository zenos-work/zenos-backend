# Pure SQL constants — no imports, no functions, no logic.
# Every query ArticleRepository uses is defined here.
# Naming convention: VERB_ENTITY_BY_FIELD

SELECT_BASE = (
    "SELECT a.*, u.name AS author_name, u.avatar_url AS author_avatar"
    " FROM articles a JOIN users u ON a.author_id = u.id"
)

SELECT_PUBLISHED_LIST = (
    SELECT_BASE + " WHERE a.status = ? AND (? = '' OR a.content_type = ?)"
    " ORDER BY a.published_at DESC LIMIT ? OFFSET ?"
)

SELECT_PUBLISHED_BY_TAG = (
    SELECT_BASE + " JOIN article_tags at ON a.id = at.article_id"
    " JOIN tags t ON at.tag_id = t.id"
    " WHERE a.status = ? AND t.slug = ? AND (? = '' OR a.content_type = ?)"
    " ORDER BY a.published_at DESC LIMIT ? OFFSET ?"
)

SELECT_PUBLISHED_SEARCH = (
    SELECT_BASE + " WHERE a.status = ?"
    " AND (? = '' OR a.content_type = ?)"
    " AND (a.title LIKE ? OR a.subtitle LIKE ?)"
    " ORDER BY a.published_at DESC LIMIT ? OFFSET ?"
)

SELECT_BY_ID_OR_SLUG = SELECT_BASE + " WHERE a.id = ? OR a.slug = ?"

SELECT_BY_AUTHOR = (
    SELECT_BASE + " WHERE a.author_id = ?"
    " ORDER BY a.updated_at DESC LIMIT ? OFFSET ?"
)

SELECT_BY_AUTHOR_AND_STATUS = (
    SELECT_BASE + " WHERE a.author_id = ? AND a.status = ?"
    " ORDER BY a.updated_at DESC LIMIT ? OFFSET ?"
)

SELECT_AUTHOR_ID_BY_ID = "SELECT author_id FROM articles WHERE id = ?"

SELECT_STATUS_BY_ID = "SELECT id, author_id, status FROM articles WHERE id = ?"

SELECT_TAGS_FOR_ARTICLE = (
    "SELECT t.* FROM tags t"
    " JOIN article_tags at ON t.id = at.tag_id"
    " WHERE at.article_id = ?"
)

INSERT_ARTICLE = (
    "INSERT INTO articles"
    " (id, author_id, title, slug, subtitle, content_type, content,"
    "  cover_image_url, read_time_minutes, status,"
    "  last_verified_at, expires_at, seo_title, seo_description, canonical_url, og_image_url, seo_schema_type)"
    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)

UPDATE_ARTICLE = (
    "UPDATE articles"
    " SET title = ?, content = ?, subtitle = ?, content_type = ?,"
    "     cover_image_url = ?, read_time_minutes = ?,"
    "     last_verified_at = ?, expires_at = ?,"
    "     seo_title = ?, seo_description = ?, canonical_url = ?, og_image_url = ?, seo_schema_type = ?,"
    '     updated_at = datetime("now")'
    " WHERE id = ?"
)

UPDATE_STATUS = (
    'UPDATE articles SET status = ?, updated_at = datetime("now")' " WHERE id = ?"
)

UPDATE_APPROVE = (
    "UPDATE articles"
    ' SET status = ?, approved_by = ?, moderation_state = ?, moderation_note = ?, updated_at = datetime("now")'
    " WHERE id = ? AND status = ?"
)

UPDATE_REJECT = (
    "UPDATE articles"
    ' SET status = ?, rejection_note = ?, moderation_state = ?, moderation_note = ?, updated_at = datetime("now")'
    " WHERE id = ?"
)

UPDATE_PUBLISH = (
    "UPDATE articles"
    ' SET status = ?, published_at = datetime("now"),'
    '     updated_at = datetime("now")'
    " WHERE id = ? AND status = ?"
)

UPDATE_MODERATION_STATE = (
    "UPDATE articles"
    ' SET moderation_state = ?, moderation_note = ?, updated_at = datetime("now")'
    " WHERE id = ?"
)

UPDATE_INCREMENT_VIEWS = (
    "UPDATE articles SET views_count = views_count + 1 WHERE id = ?"
)

UPDATE_INCREMENT_LIKES = (
    "UPDATE articles SET likes_count = likes_count + 1 WHERE id = ?"
)

UPDATE_DECREMENT_LIKES = (
    "UPDATE articles SET likes_count = MAX(0, likes_count - 1) WHERE id = ?"
)

UPDATE_INCREMENT_COMMENTS = (
    "UPDATE articles SET comments_count = comments_count + 1 WHERE id = ?"
)

DELETE_ARTICLE = "DELETE FROM articles WHERE id = ?"

INSERT_ARTICLE_TAG = (
    "INSERT OR IGNORE INTO article_tags (article_id, tag_id) VALUES (?, ?)"
)

DELETE_ARTICLE_TAGS = "DELETE FROM article_tags WHERE article_id = ?"

SELECT_APPROVER_IDS = (
    "SELECT id FROM users" " WHERE role IN ('APPROVER', 'SUPERADMIN') AND is_active = 1"
)

INSERT_NOTIFICATION = (
    "INSERT INTO notifications"
    " (id, user_id, actor_id, type, article_id, comment_id, message)"
    " VALUES (?, ?, NULLIF(?, ''), ?, NULLIF(?, ''), NULLIF(?, ''), ?)"
)

SELECT_CONTENT_TYPES_PUBLIC = (
    "SELECT slug, name"
    " FROM content_types"
    " WHERE is_active = 1"
    " ORDER BY sort_order ASC, name ASC"
)

SELECT_CONTENT_TYPE_EXISTS = (
    "SELECT 1 AS ok"
    " FROM content_types"
    " WHERE slug = ? AND is_active = 1"
    " LIMIT 1"
)
