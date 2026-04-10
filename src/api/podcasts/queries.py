"""Phase 9 Step 35 — Podcast queries."""

# ── Shows ────────────────────────────────────────────────────
LIST_SHOWS = "SELECT * FROM podcast_shows ORDER BY created_at DESC LIMIT ? OFFSET ?"
LIST_SHOWS_BY_OWNER = (
    "SELECT * FROM podcast_shows WHERE owner_id = ? ORDER BY created_at DESC"
)
GET_SHOW = "SELECT * FROM podcast_shows WHERE id = ?"
GET_SHOW_BY_SLUG = "SELECT * FROM podcast_shows WHERE slug = ?"
INSERT_SHOW = """INSERT INTO podcast_shows
    (id, owner_id, org_id, title, slug, description, cover_image_url, rss_feed_url)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
UPDATE_SHOW = """UPDATE podcast_shows SET
    title=?, description=?, cover_image_url=?, rss_feed_url=?
    WHERE id=?"""
DELETE_SHOW = "DELETE FROM podcast_shows WHERE id = ?"

# ── Episodes ─────────────────────────────────────────────────
LIST_EPISODES = "SELECT * FROM podcast_episodes WHERE show_id = ? ORDER BY episode_number DESC LIMIT ? OFFSET ?"
GET_EPISODE = "SELECT * FROM podcast_episodes WHERE id = ?"
INSERT_EPISODE = """INSERT INTO podcast_episodes
    (id, show_id, title, description, audio_url, duration_seconds,
     episode_number, transcript_article_id, published_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
UPDATE_EPISODE = """UPDATE podcast_episodes SET
    title=?, description=?, audio_url=?, duration_seconds=?,
    episode_number=?, transcript_article_id=?, published_at=?
    WHERE id=?"""
DELETE_EPISODE = "DELETE FROM podcast_episodes WHERE id = ?"
