SELECT_BY_ID = "SELECT * FROM users WHERE id = ?"

SELECT_PUBLIC_BY_ID = (
    "SELECT id, name, role, avatar_url, created_at,"
    " handle, bio, website_url, social_links, location,"
    " cover_image_url, pronouns, tagline, membership_tier"
    " FROM users WHERE id = ?"
)

SELECT_ALL_USERS = (
    "SELECT id, email, name, role, is_active, created_at"
    " FROM users ORDER BY created_at DESC"
)

SELECT_ARTICLES_BY_AUTHOR = (
    "SELECT a.*, u.name AS author_name, u.avatar_url AS author_avatar"
    " FROM articles a JOIN users u ON a.author_id = u.id"
    " WHERE a.author_id = ? AND a.status != ?"
    " ORDER BY a.updated_at DESC LIMIT ? OFFSET ?"
)

SELECT_PREFS_BY_USER = "SELECT * FROM user_preferences WHERE user_id = ?"

INSERT_PREFS = "INSERT OR IGNORE INTO user_preferences (user_id) VALUES (?)"

UPDATE_PROFILE = (
    "UPDATE users SET name = ?, avatar_url = NULLIF(?, ''),"
    " handle = COALESCE(NULLIF(?, ''), handle),"
    " bio = COALESCE(NULLIF(?, ''), bio),"
    " website_url = COALESCE(NULLIF(?, ''), website_url),"
    " social_links = COALESCE(NULLIF(?, ''), social_links),"
    " location = COALESCE(NULLIF(?, ''), location),"
    " cover_image_url = COALESCE(NULLIF(?, ''), cover_image_url),"
    " pronouns = COALESCE(NULLIF(?, ''), pronouns),"
    " tagline = COALESCE(NULLIF(?, ''), tagline),"
    ' updated_at = datetime("now") WHERE id = ?'
)

CHECK_HANDLE_UNIQUE = "SELECT id FROM users WHERE handle = ? AND id != ? LIMIT 1"

UPDATE_ROLE = "UPDATE users SET role = ?," ' updated_at = datetime("now") WHERE id = ?'

UPDATE_SELF_ROLE = "UPDATE users SET role = ?" " WHERE id = ? AND role = ?"

UPDATE_PREFS = (
    "UPDATE user_preferences SET topics = ?, email_notifs = ?, theme = ?,"
    " font_family = ?, font_size = ?, content_width = ?, line_height = ?,"
    " code_theme = ?,"
    ' updated_at = datetime("now") WHERE user_id = ?'
)

UPDATE_BAN = "UPDATE users SET is_active = 0 WHERE id = ?"

UPDATE_UNBAN = "UPDATE users SET is_active = 1 WHERE id = ?"

UPDATE_ACCEPT_TERMS = (
    "UPDATE users"
    " SET terms_accepted_at = datetime('now'),"
    "     updated_at = datetime('now')"
    " WHERE id = ? AND terms_accepted_at IS NULL"
)

SELECT_TERMS_STATUS = "SELECT terms_accepted_at FROM users WHERE id = ?"

SELECT_READING_HISTORY_BY_USER = (
    "SELECT user_id, article_id, slug, title, subtitle, author_name, cover_image_url,"
    " read_time_minutes, progress, last_read_at, created_at, updated_at"
    " FROM user_reading_history"
    " WHERE user_id = ?"
    " ORDER BY datetime(last_read_at) DESC"
    " LIMIT ? OFFSET ?"
)

COUNT_READING_HISTORY_BY_USER = (
    "SELECT COUNT(*) AS c FROM user_reading_history WHERE user_id = ?"
)

UPSERT_READING_HISTORY_ITEM = (
    "INSERT INTO user_reading_history"
    " (user_id, article_id, slug, title, subtitle, author_name, cover_image_url,"
    "  read_time_minutes, progress, last_read_at, created_at, updated_at)"
    " VALUES (?, ?, ?, ?, NULLIF(?, ''), NULLIF(?, ''), NULLIF(?, ''), ?, ?, COALESCE(NULLIF(?, ''), datetime('now')), datetime('now'), datetime('now'))"
    " ON CONFLICT(user_id, article_id) DO UPDATE SET"
    " slug = excluded.slug,"
    " title = excluded.title,"
    " subtitle = excluded.subtitle,"
    " author_name = excluded.author_name,"
    " cover_image_url = excluded.cover_image_url,"
    " read_time_minutes = excluded.read_time_minutes,"
    " progress = excluded.progress,"
    " last_read_at = excluded.last_read_at,"
    " updated_at = datetime('now')"
)

DELETE_READING_HISTORY_ITEM = (
    "DELETE FROM user_reading_history WHERE user_id = ? AND article_id = ?"
)

DELETE_READING_HISTORY_BY_USER = "DELETE FROM user_reading_history WHERE user_id = ?"
