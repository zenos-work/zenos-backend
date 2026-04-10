"""Phase 5 Step 24 — Marketing SQL queries."""

# ── Distribution Channels ────────────────────────────────────
LIST_CHANNELS = (
    "SELECT * FROM distribution_channels WHERE org_id = ? ORDER BY created_at DESC"
)
GET_CHANNEL = "SELECT * FROM distribution_channels WHERE id = ?"
INSERT_CHANNEL = """INSERT INTO distribution_channels
  (id, org_id, name, channel_type, config, kv_secret_key, is_active, created_by)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
UPDATE_CHANNEL = """UPDATE distribution_channels
  SET name = ?, channel_type = ?, config = ?, is_active = ?, updated_at = datetime('now')
  WHERE id = ?"""
DELETE_CHANNEL = "DELETE FROM distribution_channels WHERE id = ?"

# ── Scheduled Publications ───────────────────────────────────
LIST_SCHEDULED = """SELECT * FROM scheduled_publications
  WHERE scheduled_by = ? ORDER BY scheduled_at ASC"""
GET_SCHEDULED = "SELECT * FROM scheduled_publications WHERE id = ?"
GET_SCHEDULED_BY_ARTICLE = "SELECT * FROM scheduled_publications WHERE article_id = ?"
INSERT_SCHEDULED = """INSERT INTO scheduled_publications
  (id, article_id, scheduled_by, scheduled_at, timezone, status)
  VALUES (?, ?, ?, ?, ?, 'pending')"""
UPDATE_SCHEDULED_STATUS = """UPDATE scheduled_publications
  SET status = ?, published_at = ?, error_message = ? WHERE id = ?"""
DELETE_SCHEDULED = "DELETE FROM scheduled_publications WHERE id = ?"

# ── Content Distribution Jobs ────────────────────────────────
LIST_DIST_JOBS = """SELECT * FROM content_distribution_jobs
  WHERE org_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"""
GET_DIST_JOB = "SELECT * FROM content_distribution_jobs WHERE id = ?"
INSERT_DIST_JOB = """INSERT INTO content_distribution_jobs
  (id, org_id, article_id, channel_id, distribute_at, status, triggered_by_run_id)
  VALUES (?, ?, ?, ?, ?, 'pending', ?)"""
UPDATE_DIST_JOB_STATUS = """UPDATE content_distribution_jobs
  SET status = ?, external_id = ?, external_url = ?, error_message = ?,
      attempt_count = attempt_count + 1, updated_at = datetime('now')
  WHERE id = ?"""

# ── Content Syndication ──────────────────────────────────────
LIST_SYNDICATIONS = "SELECT * FROM content_syndication WHERE article_id = ?"
INSERT_SYNDICATION = """INSERT INTO content_syndication
  (id, article_id, platform, external_url, canonical_back_link)
  VALUES (?, ?, ?, ?, ?)"""
DELETE_SYNDICATION = "DELETE FROM content_syndication WHERE id = ?"

# ── RSS Feeds ────────────────────────────────────────────────
LIST_RSS_FEEDS = "SELECT * FROM rss_feeds WHERE org_id = ? ORDER BY name"
GET_RSS_FEED = "SELECT * FROM rss_feeds WHERE id = ?"
GET_RSS_FEED_BY_SLUG = "SELECT * FROM rss_feeds WHERE org_id = ? AND slug = ?"
INSERT_RSS_FEED = """INSERT INTO rss_feeds
  (id, org_id, name, slug, description, filter_tags, filter_authors,
   max_items, include_premium, is_active)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
UPDATE_RSS_FEED = """UPDATE rss_feeds
  SET name = ?, description = ?, filter_tags = ?, filter_authors = ?,
      max_items = ?, include_premium = ?, is_active = ?
  WHERE id = ?"""
DELETE_RSS_FEED = "DELETE FROM rss_feeds WHERE id = ?"

# ── Content Repurposing ──────────────────────────────────────
LIST_REPURPOSING = """SELECT * FROM content_repurposing_jobs
  WHERE org_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"""
GET_REPURPOSING = "SELECT * FROM content_repurposing_jobs WHERE id = ?"
INSERT_REPURPOSING = """INSERT INTO content_repurposing_jobs
  (id, org_id, article_id, format, status, input_options, created_by)
  VALUES (?, ?, ?, ?, 'pending', ?, ?)"""
UPDATE_REPURPOSING_STATUS = """UPDATE content_repurposing_jobs
  SET status = ?, output_content = ?, updated_at = datetime('now') WHERE id = ?"""

# ── Campaigns ────────────────────────────────────────────────
LIST_CAMPAIGNS = (
    "SELECT * FROM campaigns WHERE org_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
)
GET_CAMPAIGN = "SELECT * FROM campaigns WHERE id = ?"
INSERT_CAMPAIGN = """INSERT INTO campaigns
  (id, org_id, name, description, type, status, start_date, end_date,
   budget_cents, goal_id, created_by)
  VALUES (?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?, ?)"""
UPDATE_CAMPAIGN = """UPDATE campaigns
  SET name = ?, description = ?, status = ?, start_date = ?, end_date = ?,
      budget_cents = ?
  WHERE id = ?"""
DELETE_CAMPAIGN = "DELETE FROM campaigns WHERE id = ?"

# ── Campaign Articles ────────────────────────────────────────
LIST_CAMPAIGN_ARTICLES = (
    "SELECT article_id FROM campaign_articles WHERE campaign_id = ?"
)
ADD_CAMPAIGN_ARTICLE = (
    "INSERT OR IGNORE INTO campaign_articles (campaign_id, article_id) VALUES (?, ?)"
)
REMOVE_CAMPAIGN_ARTICLE = (
    "DELETE FROM campaign_articles WHERE campaign_id = ? AND article_id = ?"
)
