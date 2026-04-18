"""Phase 7 Step 29 — Newsletter queries."""

# ── Newsletters ──────────────────────────────────────────────
LIST_NEWSLETTERS = "SELECT * FROM newsletters WHERE org_id = ? ORDER BY created_at DESC"
LIST_NEWSLETTERS_BY_OWNER = (
    "SELECT * FROM newsletters WHERE owner_id = ? ORDER BY created_at DESC"
)
GET_NEWSLETTER = "SELECT * FROM newsletters WHERE id = ?"
GET_NEWSLETTER_BY_SLUG = "SELECT * FROM newsletters WHERE slug = ?"
INSERT_NEWSLETTER = """INSERT INTO newsletters
    (id, org_id, owner_id, name, slug, description, logo_url, cover_url,
     from_name, from_email, reply_to_email, is_premium_only, membership_tier, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
UPDATE_NEWSLETTER = """UPDATE newsletters SET
    name=?, description=?, logo_url=?, cover_url=?, from_name=?, from_email=?,
    reply_to_email=?, is_premium_only=?, membership_tier=?, status=?,
    updated_at=datetime('now') WHERE id=?"""
DELETE_NEWSLETTER = "DELETE FROM newsletters WHERE id = ?"
INCREMENT_SUBSCRIBER_COUNT = (
    "UPDATE newsletters SET subscriber_count = subscriber_count + 1 WHERE id = ?"
)
DECREMENT_SUBSCRIBER_COUNT = "UPDATE newsletters SET subscriber_count = MAX(0, subscriber_count - 1) WHERE id = ?"

# ── Subscribers ──────────────────────────────────────────────
LIST_SUBSCRIBERS = """SELECT * FROM newsletter_subscribers
    WHERE newsletter_id = ? ORDER BY subscribed_at DESC LIMIT ? OFFSET ?"""
GET_SUBSCRIBER = "SELECT * FROM newsletter_subscribers WHERE id = ?"
GET_SUBSCRIBER_BY_EMAIL = (
    "SELECT * FROM newsletter_subscribers WHERE newsletter_id = ? AND email = ?"
)
INSERT_SUBSCRIBER = """INSERT INTO newsletter_subscribers
    (id, newsletter_id, email, first_name, last_name, source, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)"""
UPDATE_SUBSCRIBER_STATUS = "UPDATE newsletter_subscribers SET status = ?, unsubscribed_at = CASE WHEN ? = 'unsubscribed' THEN datetime('now') ELSE unsubscribed_at END WHERE id = ?"
DELETE_SUBSCRIBER = "DELETE FROM newsletter_subscribers WHERE id = ?"

# ── Issues ───────────────────────────────────────────────────
LIST_ISSUES = """SELECT * FROM newsletter_issues
    WHERE newsletter_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"""
GET_ISSUE = "SELECT * FROM newsletter_issues WHERE id = ?"
INSERT_ISSUE = """INSERT INTO newsletter_issues
    (id, newsletter_id, subject, preview_text, body_html, body_text,
     issue_type, article_ids, status, scheduled_at, created_by)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
UPDATE_ISSUE = """UPDATE newsletter_issues SET
    subject=?, preview_text=?, body_html=?, body_text=?,
    issue_type=?, article_ids=?, status=?, scheduled_at=?,
    updated_at=datetime('now') WHERE id=?"""
UPDATE_ISSUE_STATUS = """UPDATE newsletter_issues SET
    status=?, sent_at=CASE WHEN ?='sent' THEN datetime('now') ELSE sent_at END,
    updated_at=datetime('now') WHERE id=?"""
DELETE_ISSUE = "DELETE FROM newsletter_issues WHERE id = ?"

# ── Issue Articles ───────────────────────────────────────────
LIST_ISSUE_ARTICLES = (
    "SELECT * FROM newsletter_issue_articles WHERE issue_id = ? ORDER BY sort_order"
)
INSERT_ISSUE_ARTICLE = "INSERT INTO newsletter_issue_articles (issue_id, article_id, sort_order, blurb) VALUES (?, ?, ?, ?)"
DELETE_ISSUE_ARTICLE = (
    "DELETE FROM newsletter_issue_articles WHERE issue_id = ? AND article_id = ?"
)

# ── Send Events ──────────────────────────────────────────────
LIST_SEND_EVENTS = """SELECT * FROM newsletter_send_events
    WHERE issue_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"""
INSERT_SEND_EVENT = """INSERT INTO newsletter_send_events
    (id, issue_id, subscriber_id, event_type, link_url, metadata)
    VALUES (?, ?, ?, ?, ?, ?)"""

# ── Segments ─────────────────────────────────────────────────
LIST_SEGMENTS = "SELECT * FROM newsletter_segments WHERE newsletter_id = ?"
GET_SEGMENT = "SELECT * FROM newsletter_segments WHERE id = ?"
INSERT_SEGMENT = "INSERT INTO newsletter_segments (id, newsletter_id, name, filter_rules) VALUES (?, ?, ?, ?)"
UPDATE_SEGMENT = "UPDATE newsletter_segments SET name=?, filter_rules=? WHERE id=?"
DELETE_SEGMENT = "DELETE FROM newsletter_segments WHERE id = ?"
