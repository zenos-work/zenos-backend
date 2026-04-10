# ── LIKES ──────────────────────────────────
INSERT_LIKE = "INSERT INTO likes (user_id, article_id) VALUES (?, ?)"
DELETE_LIKE = "DELETE FROM likes WHERE user_id = ? AND article_id = ?"
SELECT_IF_LIKED = "SELECT 1 FROM likes WHERE user_id = ? AND article_id = ? LIMIT 1"
COUNT_LIKES = "SELECT COUNT(*) as count FROM likes WHERE article_id = ?"

# ── DISLIKES ───────────────────────────────
INSERT_DISLIKE = "INSERT INTO article_dislikes (user_id, article_id) VALUES (?, ?)"
DELETE_DISLIKE = "DELETE FROM article_dislikes WHERE user_id = ? AND article_id = ?"
SELECT_IF_DISLIKED = (
    "SELECT 1 FROM article_dislikes WHERE user_id = ? AND article_id = ? LIMIT 1"
)
COUNT_DISLIKES = "SELECT COUNT(*) as count FROM article_dislikes WHERE article_id = ?"

# ── SHARES ────────────────────────────────
INSERT_SHARE = (
    "INSERT INTO article_shares (id, user_id, article_id, provider) VALUES (?, ?, ?, ?)"
)
COUNT_SHARES = "SELECT COUNT(*) as count FROM article_shares WHERE article_id = ?"

# ── REACTIONS ─────────────────────────────
INSERT_REACTION = "INSERT INTO article_reactions (article_id, user_id, reaction_type) VALUES (?, ?, ?)"
DELETE_REACTION = "DELETE FROM article_reactions WHERE article_id = ? AND user_id = ? AND reaction_type = ?"
SELECT_IF_REACTED = "SELECT 1 FROM article_reactions WHERE article_id = ? AND user_id = ? AND reaction_type = ? LIMIT 1"
SELECT_REACTION_COUNTS = (
    "SELECT"
    " SUM(CASE WHEN reaction_type = 'fire' THEN 1 ELSE 0 END) AS fire_count,"
    " SUM(CASE WHEN reaction_type = 'lightbulb' THEN 1 ELSE 0 END) AS lightbulb_count,"
    " SUM(CASE WHEN reaction_type = 'heart' THEN 1 ELSE 0 END) AS heart_count,"
    " SUM(CASE WHEN reaction_type = 'brain' THEN 1 ELSE 0 END) AS brain_count"
    " FROM article_reactions"
    " WHERE article_id = ?"
)
SELECT_USER_REACTIONS = (
    "SELECT reaction_type FROM article_reactions WHERE article_id = ? AND user_id = ?"
)

# ── BOOKMARKS ──────────────────────────────
INSERT_BOOKMARK = "INSERT INTO bookmarks (user_id, article_id) VALUES (?, ?)"
DELETE_BOOKMARK = "DELETE FROM bookmarks WHERE user_id = ? AND article_id = ?"
SELECT_IF_BOOKMARKED = (
    "SELECT 1 FROM bookmarks WHERE user_id = ? AND article_id = ? LIMIT 1"
)
SELECT_BOOKMARKS_BY_USER = (
    "SELECT a.*, u.name AS author_name, u.avatar_url AS author_avatar"
    " FROM articles a JOIN bookmarks b ON a.id = b.article_id"
    " JOIN users u ON a.author_id = u.id"
    " WHERE b.user_id = ? ORDER BY b.created_at DESC LIMIT ? OFFSET ?"
)
COUNT_BOOKMARKS = "SELECT COUNT(*) as count FROM bookmarks WHERE user_id = ?"

# ── FOLLOWS ────────────────────────────────
INSERT_FOLLOW = (
    "INSERT INTO follows (follower_id, following_id, following_type)"
    " VALUES (?, ?, COALESCE(NULLIF(?, ''), 'user'))"
)
DELETE_FOLLOW = (
    "DELETE FROM follows WHERE follower_id = ? AND following_id = ?"
    " AND following_type = COALESCE(NULLIF(?, ''), 'user')"
)
SELECT_IF_FOLLOWING = (
    "SELECT 1 FROM follows WHERE follower_id = ? AND following_id = ?"
    " AND following_type = COALESCE(NULLIF(?, ''), 'user') LIMIT 1"
)
SELECT_FOLLOWERS = (
    "SELECT u.* FROM users u"
    " JOIN follows f ON u.id = f.follower_id"
    " WHERE f.following_id = ? AND f.following_type = 'user'"
    " ORDER BY f.created_at DESC LIMIT ? OFFSET ?"
)
COUNT_FOLLOWERS = (
    "SELECT COUNT(*) as count FROM follows"
    " WHERE following_id = ? AND following_type = 'user'"
)
SELECT_FOLLOWING = (
    "SELECT u.* FROM users u"
    " JOIN follows f ON u.id = f.following_id"
    " WHERE f.follower_id = ? AND f.following_type = 'user'"
    " ORDER BY f.created_at DESC LIMIT ? OFFSET ?"
)
COUNT_FOLLOWING = (
    "SELECT COUNT(*) as count FROM follows"
    " WHERE follower_id = ? AND following_type = 'user'"
)
SELECT_FOLLOWING_IDS = (
    "SELECT following_id FROM follows WHERE follower_id = ? AND following_type = 'user'"
)
SELECT_FOLLOWERS_COUNT = (
    "SELECT COUNT(*) AS c FROM follows"
    " WHERE following_id = ? AND following_type = 'user'"
)
