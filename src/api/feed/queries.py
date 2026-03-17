_BASE = (
    "SELECT a.*, u.name AS author_name, u.avatar_url AS author_avatar"
    " FROM articles a JOIN users u ON a.author_id = u.id"
)

SELECT_FEED_LATEST = (
    _BASE + " WHERE a.status = ?" " ORDER BY a.published_at DESC LIMIT ? OFFSET ?"
)

SELECT_FEED_BY_TOPICS = (
    "SELECT DISTINCT a.*, u.name AS author_name, u.avatar_url AS author_avatar"
    " FROM articles a JOIN users u ON a.author_id = u.id"
    " JOIN article_tags at ON a.id = at.article_id"
    " JOIN tags t ON at.tag_id = t.id"
    " WHERE a.status = ?"
    "   AND t.slug IN (SELECT value FROM json_each(?))"
    " ORDER BY a.published_at DESC LIMIT ? OFFSET ?"
)

SELECT_FEED_FOLLOWING = (
    _BASE + " JOIN follows f ON a.author_id = f.following_id"
    " WHERE f.follower_id = ? AND a.status = ?"
    " ORDER BY a.published_at DESC LIMIT ? OFFSET ?"
)

SELECT_FEED_FEATURED = (
    _BASE + " WHERE a.status = ? AND a.is_featured = 1"
    " ORDER BY a.published_at DESC LIMIT 10"
)
