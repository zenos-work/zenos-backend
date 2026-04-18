COUNT_ACTIVE_USERS = "SELECT COUNT(*) AS c FROM users WHERE is_active = 1"

COUNT_USERS_TOTAL = "SELECT COUNT(*) AS c FROM users"

COUNT_USERS_BY_ROLE = "SELECT role, COUNT(*) AS c FROM users GROUP BY role"

COUNT_ARTICLES_BY_STATUS = "SELECT status, COUNT(*) AS c FROM articles GROUP BY status"

COUNT_ACTIVE_COMMENTS = "SELECT COUNT(*) AS c FROM comments WHERE is_deleted = 0"

COUNT_TOTAL_SHARES = "SELECT COALESCE(SUM(shares_count), 0) AS c FROM articles"

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
    " ORDER BY a.updated_at DESC LIMIT ? OFFSET ?"
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
    " (id, user_id, actor_id, type, article_id, comment_id, message,"
    "  channel, delivery_status, group_key)"
    " VALUES (?, ?, NULLIF(?, ''), ?, NULLIF(?, ''), NULLIF(?, ''), ?,"
    "  COALESCE(NULLIF(?, ''), 'in_app'), 'pending', NULLIF(?, ''))"
)

UPDATE_MARK_NOTIFICATIONS_READ = (
    "UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0"
)

UPDATE_MARK_NOTIFICATION_READ_BY_ID = (
    "UPDATE notifications SET is_read = 1 WHERE user_id = ? AND id = ? AND is_read = 0"
)

DELETE_ALL_NOTIFICATIONS = "DELETE FROM notifications WHERE user_id = ?"

DELETE_NOTIFICATION = "DELETE FROM notifications WHERE user_id = ? AND id = ?"

SELECT_CONTENT_TYPES_ADMIN = (
    "SELECT id, slug, name, description, is_active, is_system, sort_order, created_by, created_at, updated_at"
    " FROM content_types"
    " ORDER BY sort_order ASC, name ASC"
)

SELECT_CONTENT_TYPE_BY_SLUG = (
    "SELECT id, slug, name, description, is_active, is_system, sort_order, created_by, created_at, updated_at"
    " FROM content_types"
    " WHERE slug = ?"
    " LIMIT 1"
)

INSERT_CONTENT_TYPE = (
    "INSERT INTO content_types (id, slug, name, description, is_active, is_system, sort_order, created_by)"
    " VALUES (?, ?, ?, ?, 1, 0, ?, ?)"
)

SELECT_SUCCESS_SIGNALS_HOURLY = (
    "SELECT s.article_id, a.slug, a.title, s.bucket_hour,"
    " s.views_count, s.likes_count, s.comments_count, s.outcome_events_count,"
    " s.outcome_tag_count, s.engagement_score, s.success_rate, s.updated_at"
    " FROM article_success_hourly s"
    " JOIN articles a ON a.id = s.article_id"
    " ORDER BY s.bucket_hour DESC, s.success_rate DESC"
    " LIMIT ? OFFSET ?"
)

COUNT_SUCCESS_SIGNALS_HOURLY = "SELECT COUNT(*) AS c FROM article_success_hourly"

SELECT_SUCCESS_SIGNAL_HISTORY_BY_ARTICLE = (
    "SELECT bucket_hour, success_rate, engagement_score"
    " FROM article_success_hourly"
    " WHERE article_id = ?"
    " ORDER BY bucket_hour DESC"
    " LIMIT ?"
)

# ── Notification delivery dispatch ────────────────────────────────────────────

SELECT_PENDING_DELIVERY_BY_CHANNEL = (
    "SELECT n.id, n.user_id, n.message, n.type, n.group_key, n.channel,"
    "       u.email AS user_email, u.name AS user_name"
    " FROM notifications n"
    " JOIN users u ON u.id = n.user_id"
    " WHERE n.delivery_status = 'pending'"
    "   AND n.channel = ?"
    " ORDER BY n.created_at ASC"
    " LIMIT ?"
)

# Placeholders filled in by repository: e.g. "?,?,?"
SELECT_PUSH_SUBS_FOR_USERS = (
    "SELECT ps.user_id, ps.endpoint, ps.p256dh_key, ps.auth_key, ps.platform"
    " FROM push_subscriptions ps"
    " WHERE ps.is_active = 1"
    "   AND ps.user_id IN ({placeholders})"
)

UPDATE_NOTIFICATION_DELIVERY_STATUS = (
    "UPDATE notifications"
    " SET delivery_status = ?,"
    "     delivered_at = CASE WHEN ? = 'delivered' THEN datetime('now') ELSE NULL END,"
    "     external_ref = COALESCE(NULLIF(?, ''), external_ref)"
    " WHERE id = ?"
)

SELECT_RANKING_WEIGHTS = (
    "SELECT likes_weight, shares_weight, comments_weight, dislikes_weight,"
    " views_weight, recency_weight, updated_by, updated_at"
    " FROM ranking_weights"
    " WHERE id = 1"
    " LIMIT 1"
)

UPSERT_RANKING_WEIGHTS = (
    "INSERT INTO ranking_weights"
    " (id, likes_weight, shares_weight, comments_weight, dislikes_weight, views_weight, recency_weight, updated_by, updated_at)"
    " VALUES (1, ?, ?, ?, ?, ?, ?, ?, datetime('now'))"
    " ON CONFLICT(id) DO UPDATE SET"
    " likes_weight = excluded.likes_weight,"
    " shares_weight = excluded.shares_weight,"
    " comments_weight = excluded.comments_weight,"
    " dislikes_weight = excluded.dislikes_weight,"
    " views_weight = excluded.views_weight,"
    " recency_weight = excluded.recency_weight,"
    " updated_by = excluded.updated_by,"
    " updated_at = datetime('now')"
)

SELECT_RANKED_CONTENT_TYPES = (
    "WITH w AS ("
    "  SELECT likes_weight, shares_weight, comments_weight, dislikes_weight, views_weight, recency_weight"
    "  FROM ranking_weights WHERE id = 1"
    "), scored AS ("
    "  SELECT a.content_type,"
    "         a.likes_count,"
    "         COALESCE(a.dislikes_count, 0) AS dislikes_count,"
    "         a.shares_count,"
    "         a.comments_count,"
    "         a.views_count,"
    "         ((a.likes_count * w.likes_weight)"
    "          + (COALESCE(a.dislikes_count, 0) * w.dislikes_weight)"
    "          + (a.shares_count * w.shares_weight)"
    "          + (a.comments_count * w.comments_weight)"
    "          + (a.views_count * w.views_weight)"
    "          + ((1.0 / (1.0 + MAX(0, julianday('now') - julianday(COALESCE(a.published_at, a.updated_at, a.created_at))))) * 100.0 * w.recency_weight)"
    "         ) AS score"
    "  FROM articles a CROSS JOIN w"
    "  WHERE a.status = 'PUBLISHED'"
    ")"
    " SELECT content_type,"
    "        COUNT(*) AS articles_count,"
    "        ROUND(SUM(score), 2) AS total_score,"
    "        ROUND(AVG(score), 2) AS avg_score,"
    "        SUM(likes_count) AS likes_count,"
    "        SUM(dislikes_count) AS dislikes_count,"
    "        SUM(shares_count) AS shares_count,"
    "        SUM(comments_count) AS comments_count,"
    "        SUM(views_count) AS views_count"
    " FROM scored"
    " GROUP BY content_type"
    " ORDER BY avg_score DESC, total_score DESC"
    " LIMIT ?"
)

SELECT_RANKED_CATEGORIES = (
    "WITH w AS ("
    "  SELECT likes_weight, shares_weight, comments_weight, dislikes_weight, views_weight, recency_weight"
    "  FROM ranking_weights WHERE id = 1"
    "), scored AS ("
    "  SELECT a.id AS article_id,"
    "         COALESCE(NULLIF(t.category_slug, ''), t.slug) AS category_slug,"
    "         t.name AS category_name,"
    "         a.likes_count,"
    "         COALESCE(a.dislikes_count, 0) AS dislikes_count,"
    "         a.shares_count,"
    "         a.comments_count,"
    "         a.views_count,"
    "         ((a.likes_count * w.likes_weight)"
    "          + (COALESCE(a.dislikes_count, 0) * w.dislikes_weight)"
    "          + (a.shares_count * w.shares_weight)"
    "          + (a.comments_count * w.comments_weight)"
    "          + (a.views_count * w.views_weight)"
    "          + ((1.0 / (1.0 + MAX(0, julianday('now') - julianday(COALESCE(a.published_at, a.updated_at, a.created_at))))) * 100.0 * w.recency_weight)"
    "         ) AS score"
    "  FROM articles a"
    "  JOIN article_tags at ON at.article_id = a.id"
    "  JOIN tags t ON t.id = at.tag_id"
    "  CROSS JOIN w"
    "  WHERE a.status = 'PUBLISHED' AND t.tag_type = 'topic'"
    ")"
    " SELECT category_slug,"
    "        MAX(category_name) AS category_name,"
    "        COUNT(DISTINCT article_id) AS articles_count,"
    "        ROUND(SUM(score), 2) AS total_score,"
    "        ROUND(AVG(score), 2) AS avg_score,"
    "        SUM(likes_count) AS likes_count,"
    "        SUM(dislikes_count) AS dislikes_count,"
    "        SUM(shares_count) AS shares_count,"
    "        SUM(comments_count) AS comments_count,"
    "        SUM(views_count) AS views_count"
    " FROM scored"
    " GROUP BY category_slug"
    " ORDER BY avg_score DESC, total_score DESC"
    " LIMIT ?"
)
