# Pure SQL constants — no imports, no functions, no logic.
# Naming convention: VERB_ENTITY_BY_FIELD

_BASE = (
    "SELECT a.*, u.name AS author_name, u.avatar_url AS author_avatar"
    " FROM articles a JOIN users u ON a.author_id = u.id"
)

# ── LATEST ──────────────────────────────────────────────────────────
SELECT_FEED_LATEST = (
    _BASE + " WHERE a.status = ? ORDER BY a.published_at DESC LIMIT ? OFFSET ?"
)

COUNT_FEED_LATEST = "SELECT COUNT(*) AS c FROM articles WHERE status = ?"

# ── BY TOPICS (personalised) ─────────────────────────────────────────
SELECT_FEED_BY_TOPICS = (
    "SELECT DISTINCT a.*, u.name AS author_name, u.avatar_url AS author_avatar"
    " FROM articles a JOIN users u ON a.author_id = u.id"
    " JOIN article_tags at ON a.id = at.article_id"
    " JOIN tags t ON at.tag_id = t.id"
    " WHERE a.status = ?"
    "   AND t.slug IN (SELECT value FROM json_each(?))"
    " ORDER BY a.published_at DESC LIMIT ? OFFSET ?"
)

COUNT_FEED_BY_TOPICS = (
    "SELECT COUNT(DISTINCT a.id) AS c"
    " FROM articles a"
    " JOIN article_tags at ON a.id = at.article_id"
    " JOIN tags t ON at.tag_id = t.id"
    " WHERE a.status = ?"
    "   AND t.slug IN (SELECT value FROM json_each(?))"
)

# ── FOLLOWING ────────────────────────────────────────────────────────
SELECT_FEED_FOLLOWING = (
    _BASE + " JOIN follows f ON a.author_id = f.following_id"
    " WHERE f.follower_id = ? AND a.status = ?"
    " ORDER BY a.published_at DESC LIMIT ? OFFSET ?"
)

COUNT_FEED_FOLLOWING = (
    "SELECT COUNT(*) AS c FROM articles a"
    " JOIN follows f ON a.author_id = f.following_id"
    " WHERE f.follower_id = ? AND a.status = ?"
)

# ── FEATURED ─────────────────────────────────────────────────────────
SELECT_FEED_FEATURED = (
    _BASE + " WHERE a.status = ? AND a.is_featured = 1"
    " ORDER BY a.published_at DESC LIMIT 10"
)

# ── TRENDING (engagement-scored) ─────────────────────────────────────
# Score formula (Hacker-News-style):
#   score = (likes_count + comments_count * 2 + views_count * 0.5)
#           / (hours_since_publish + 2) ^ 1.5
# Only considers articles published in the last 7 days to keep it fresh.
SELECT_FEED_TRENDING = (
    "SELECT a.*, u.name AS author_name, u.avatar_url AS author_avatar,"
    "  CAST("
    "    (a.likes_count + a.comments_count * 2.0 + a.views_count * 0.5)"
    "    / ((((strftime('%s', 'now') - strftime('%s', a.published_at)) / 3600.0) + 2) * 1.5)"
    "  AS REAL) AS score"
    " FROM articles a JOIN users u ON a.author_id = u.id"
    " WHERE a.status = ?"
    "   AND a.published_at >= datetime('now', '-7 days')"
    " ORDER BY score DESC LIMIT ? OFFSET ?"
)

COUNT_FEED_TRENDING = (
    "SELECT COUNT(*) AS c FROM articles"
    " WHERE status = ?"
    "   AND published_at >= datetime('now', '-7 days')"
)

# ── RECOMMENDED (interest + follows + engagement) ────────────────────
# Strategy:
# 1) explicit preference topics from user profile (highest weight)
# 2) inferred topics from likes and bookmarks (behavioral signal)
# 3) followed authors boost
# 4) recent engagement freshness score
_RECOMMENDATION_CTE = (
    "WITH explicit_topics AS ("
    "   SELECT value AS slug, 5.0 AS weight FROM json_each(?)"
    "),"
    " liked_topics AS ("
    "   SELECT t.slug AS slug, 3.0 AS weight"
    "   FROM likes l"
    "   JOIN article_tags at ON l.article_id = at.article_id"
    "   JOIN tags t ON t.id = at.tag_id"
    "   WHERE l.user_id = ?"
    "),"
    " bookmarked_topics AS ("
    "   SELECT t.slug AS slug, 2.0 AS weight"
    "   FROM bookmarks b"
    "   JOIN article_tags at ON b.article_id = at.article_id"
    "   JOIN tags t ON t.id = at.tag_id"
    "   WHERE b.user_id = ?"
    "),"
    " topic_weights AS ("
    "   SELECT slug, SUM(weight) AS weight"
    "   FROM ("
    "     SELECT slug, weight FROM explicit_topics"
    "     UNION ALL"
    "     SELECT slug, weight FROM liked_topics"
    "     UNION ALL"
    "     SELECT slug, weight FROM bookmarked_topics"
    "   )"
    "   GROUP BY slug"
    ")"
)

SELECT_FEED_RECOMMENDED = (
    _RECOMMENDATION_CTE + " SELECT"
    "   a.*,"
    "   u.name AS author_name,"
    "   u.avatar_url AS author_avatar,"
    "   COALESCE(SUM(tw.weight), 0.0) AS topic_score,"
    "   CASE"
    "     WHEN EXISTS ("
    "       SELECT 1"
    "       FROM follows f"
    "       WHERE f.follower_id = ? AND f.following_id = a.author_id"
    "     ) THEN 4.0"
    "     ELSE 0.0"
    "   END AS follow_score,"
    "   CAST("
    "     (a.likes_count + a.comments_count * 2.0 + a.views_count * 0.25)"
    "     / ((((strftime('%s', 'now') - strftime('%s', COALESCE(a.published_at, a.created_at))) / 3600.0) + 2.0) * 1.25)"
    "   AS REAL) AS engagement_score"
    " FROM articles a"
    " JOIN users u ON a.author_id = u.id"
    " LEFT JOIN article_tags at ON a.id = at.article_id"
    " LEFT JOIN tags t ON at.tag_id = t.id"
    " LEFT JOIN topic_weights tw ON tw.slug = t.slug"
    " WHERE a.status = ?"
    " GROUP BY a.id"
    " HAVING (topic_score > 0 OR follow_score > 0)"
    " ORDER BY (topic_score * 2.0 + follow_score + engagement_score) DESC, a.published_at DESC"
    " LIMIT ? OFFSET ?"
)

COUNT_FEED_RECOMMENDED = (
    _RECOMMENDATION_CTE + " SELECT COUNT(*) AS c FROM ("
    "   SELECT a.id,"
    "     COALESCE(SUM(tw.weight), 0.0) AS topic_score,"
    "     CASE"
    "       WHEN EXISTS ("
    "         SELECT 1"
    "         FROM follows f"
    "         WHERE f.follower_id = ? AND f.following_id = a.author_id"
    "       ) THEN 4.0"
    "       ELSE 0.0"
    "     END AS follow_score"
    "   FROM articles a"
    "   LEFT JOIN article_tags at ON a.id = at.article_id"
    "   LEFT JOIN tags t ON at.tag_id = t.id"
    "   LEFT JOIN topic_weights tw ON tw.slug = t.slug"
    "   WHERE a.status = ?"
    "   GROUP BY a.id"
    "   HAVING (topic_score > 0 OR follow_score > 0)"
    " )"
)
