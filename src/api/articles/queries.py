# Pure SQL constants — no imports, no functions, no logic.
# Every query ArticleRepository uses is defined here.
# Naming convention: VERB_ENTITY_BY_FIELD

SELECT_BASE = (
    "SELECT a.*, u.name AS author_name, u.avatar_url AS author_avatar"
    " FROM articles a JOIN users u ON a.author_id = u.id"
)

SELECT_PUBLISHED_LIST_NEWEST = (
    SELECT_BASE + " WHERE a.status = ? AND (? = '' OR a.content_type = ?)"
    " ORDER BY a.published_at DESC LIMIT ? OFFSET ?"
)

SELECT_PUBLISHED_LIST_TRENDING = (
    SELECT_BASE + " WHERE a.status = ? AND (? = '' OR a.content_type = ?)"
    " ORDER BY (a.likes_count * 3 + a.comments_count * 2 + a.shares_count * 4 + a.views_count * 0.02 - a.dislikes_count * 2) DESC, a.published_at DESC LIMIT ? OFFSET ?"
)

SELECT_PUBLISHED_LIST_RECOMMENDED = (
    SELECT_BASE + " WHERE a.status = ? AND (? = '' OR a.content_type = ?)"
    " ORDER BY ((a.likes_count + a.comments_count + a.shares_count + 1.0) / (a.views_count + 1.0)) DESC, a.published_at DESC LIMIT ? OFFSET ?"
)

SELECT_PUBLISHED_BY_TAG_NEWEST = (
    SELECT_BASE + " JOIN article_tags at ON a.id = at.article_id"
    " JOIN tags t ON at.tag_id = t.id"
    " WHERE a.status = ? AND t.slug = ? AND (? = '' OR a.content_type = ?)"
    " ORDER BY a.published_at DESC LIMIT ? OFFSET ?"
)

SELECT_PUBLISHED_BY_TAG_TRENDING = (
    SELECT_BASE + " JOIN article_tags at ON a.id = at.article_id"
    " JOIN tags t ON at.tag_id = t.id"
    " WHERE a.status = ? AND t.slug = ? AND (? = '' OR a.content_type = ?)"
    " ORDER BY (a.likes_count * 3 + a.comments_count * 2 + a.shares_count * 4 + a.views_count * 0.02 - a.dislikes_count * 2) DESC, a.published_at DESC LIMIT ? OFFSET ?"
)

SELECT_PUBLISHED_BY_TAG_RECOMMENDED = (
    SELECT_BASE + " JOIN article_tags at ON a.id = at.article_id"
    " JOIN tags t ON at.tag_id = t.id"
    " WHERE a.status = ? AND t.slug = ? AND (? = '' OR a.content_type = ?)"
    " ORDER BY ((a.likes_count + a.comments_count + a.shares_count + 1.0) / (a.views_count + 1.0)) DESC, a.published_at DESC LIMIT ? OFFSET ?"
)

SELECT_PUBLISHED_SEARCH_NEWEST = (
    SELECT_BASE + " WHERE a.status = ?"
    " AND (? = '' OR a.content_type = ?)"
    " AND (a.title LIKE ? OR a.subtitle LIKE ?)"
    " ORDER BY a.published_at DESC LIMIT ? OFFSET ?"
)

SELECT_PUBLISHED_SEARCH_TRENDING = (
    SELECT_BASE + " WHERE a.status = ?"
    " AND (? = '' OR a.content_type = ?)"
    " AND (a.title LIKE ? OR a.subtitle LIKE ?)"
    " ORDER BY (a.likes_count * 3 + a.comments_count * 2 + a.shares_count * 4 + a.views_count * 0.02 - a.dislikes_count * 2) DESC, a.published_at DESC LIMIT ? OFFSET ?"
)

SELECT_PUBLISHED_SEARCH_RECOMMENDED = (
    SELECT_BASE + " WHERE a.status = ?"
    " AND (? = '' OR a.content_type = ?)"
    " AND (a.title LIKE ? OR a.subtitle LIKE ?)"
    " ORDER BY ((a.likes_count + a.comments_count + a.shares_count + 1.0) / (a.views_count + 1.0)) DESC, a.published_at DESC LIMIT ? OFFSET ?"
)

# Backward-compatible aliases used by tests/mocks and older call sites.
SELECT_PUBLISHED_LIST = SELECT_PUBLISHED_LIST_NEWEST
SELECT_PUBLISHED_BY_TAG = SELECT_PUBLISHED_BY_TAG_NEWEST
SELECT_PUBLISHED_SEARCH = SELECT_PUBLISHED_SEARCH_NEWEST

SELECT_BY_ID_OR_SLUG = SELECT_BASE + " WHERE a.id = ? OR a.slug = ?"

SELECT_BY_AUTHOR = (
    SELECT_BASE + " WHERE a.author_id = ? ORDER BY a.updated_at DESC LIMIT ? OFFSET ?"
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
    "  cover_image_url, read_time_minutes, reading_level, status,"
    "  last_verified_at, expires_at, seo_title, seo_description, canonical_url, og_image_url, seo_schema_type, citations)"
    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULLIF(?, ''), ?, ?, ?, ?, ?, ?, ?, ?, NULLIF(?, ''))"
)

UPDATE_ARTICLE = (
    "UPDATE articles"
    " SET title = ?, content = ?, subtitle = ?, content_type = ?,"
    "     cover_image_url = ?, read_time_minutes = ?, reading_level = NULLIF(?, ''),"
    "     last_verified_at = ?, expires_at = ?,"
    "     seo_title = ?, seo_description = ?, canonical_url = ?, og_image_url = ?, seo_schema_type = ?, citations = NULLIF(?, ''),"
    '     updated_at = datetime("now")'
    " WHERE id = ?"
)

UPDATE_STATUS = (
    'UPDATE articles SET status = ?, updated_at = datetime("now") WHERE id = ?'
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

UPDATE_INCREMENT_DISLIKES = (
    "UPDATE articles SET dislikes_count = dislikes_count + 1 WHERE id = ?"
)

UPDATE_DECREMENT_DISLIKES = (
    "UPDATE articles SET dislikes_count = MAX(0, dislikes_count - 1) WHERE id = ?"
)

UPDATE_INCREMENT_SHARES = (
    "UPDATE articles SET shares_count = shares_count + 1 WHERE id = ?"
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
    "SELECT id FROM users WHERE role IN ('APPROVER', 'SUPERADMIN') AND is_active = 1"
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
    "SELECT 1 AS ok FROM content_types WHERE slug = ? AND is_active = 1 LIMIT 1"
)

# Phase 2: Related articles by sharing tags, trending sort
SELECT_RELATED_ARTICLES = (
    SELECT_BASE + " JOIN article_tags at ON a.id = at.article_id"
    " JOIN article_tags at2 ON at.tag_id = at2.tag_id"
    " WHERE at2.article_id = ? AND a.id != ? AND a.status = ?"
    " GROUP BY a.id"
    " ORDER BY (a.likes_count * 3 + a.comments_count * 2 + a.shares_count * 4 - a.dislikes_count * 2 + a.views_count * 0.02) DESC,"
    "          a.published_at DESC"
    " LIMIT ?"
)

# ── Phase 3 Step 18: Security-level aware queries ──────────────────────────
# Public-only feed: appends to published list queries
SELECT_PUBLISHED_PUBLIC_ONLY = (
    SELECT_BASE + " WHERE a.status = 'PUBLISHED' AND a.security_level = 'public'"
    " ORDER BY a.published_at DESC LIMIT ? OFFSET ?"
)

# Org-member aware query: returns articles the user can see within an org
SELECT_ORG_ARTICLES = (
    SELECT_BASE + " WHERE a.org_id = ? AND a.status = 'PUBLISHED'"
    " AND (a.security_level = 'public'"
    "  OR (a.security_level = 'internal')"
    "  OR (a.security_level = 'confidential'"
    "      AND (a.author_id = ? OR EXISTS ("
    "        SELECT 1 FROM org_members om"
    "        WHERE om.org_id = a.org_id AND om.user_id = ?"
    "        AND om.org_role IN ('owner','admin','editor'))))"
    "  OR (a.security_level = 'restricted'"
    "      AND EXISTS ("
    "        SELECT 1 FROM org_members om"
    "        WHERE om.org_id = a.org_id AND om.user_id = ?"
    "        AND om.org_role IN ('owner','admin')))"
    " )"
    " ORDER BY a.published_at DESC LIMIT ? OFFSET ?"
)
