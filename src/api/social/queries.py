# ── LIKES ──────────────────────────────────
INSERT_LIKE = "INSERT INTO likes (user_id, article_id) VALUES (?, ?)"
DELETE_LIKE = "DELETE FROM likes WHERE user_id = ? AND article_id = ?"
SELECT_IF_LIKED = "SELECT 1 FROM likes WHERE user_id = ? AND article_id = ? LIMIT 1"
COUNT_LIKES = "SELECT COUNT(*) as count FROM likes WHERE article_id = ?"

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
INSERT_FOLLOW = "INSERT INTO follows (follower_id, following_id) VALUES (?, ?)"
DELETE_FOLLOW = "DELETE FROM follows WHERE follower_id = ? AND following_id = ?"
SELECT_IF_FOLLOWING = (
    "SELECT 1 FROM follows WHERE follower_id = ? AND following_id = ? LIMIT 1"
)
SELECT_FOLLOWERS = (
    "SELECT u.* FROM users u"
    " JOIN follows f ON u.id = f.follower_id"
    " WHERE f.following_id = ?"
    " ORDER BY f.created_at DESC LIMIT ? OFFSET ?"
)
COUNT_FOLLOWERS = "SELECT COUNT(*) as count FROM follows WHERE following_id = ?"
SELECT_FOLLOWING = (
    "SELECT u.* FROM users u"
    " JOIN follows f ON u.id = f.following_id"
    " WHERE f.follower_id = ?"
    " ORDER BY f.created_at DESC LIMIT ? OFFSET ?"
)
COUNT_FOLLOWING = "SELECT COUNT(*) as count FROM follows WHERE follower_id = ?"
SELECT_FOLLOWING_IDS = "SELECT following_id FROM follows WHERE follower_id = ?"
SELECT_FOLLOWERS_COUNT = "SELECT COUNT(*) AS c FROM follows WHERE following_id = ?"
