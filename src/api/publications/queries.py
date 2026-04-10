"""Phase 7 Step 30 — Publication queries."""

# ── Newsletter Subscriptions (global) ────────────────────────
LIST_SUBSCRIPTIONS = (
    "SELECT * FROM newsletter_subscriptions ORDER BY created_at DESC LIMIT ? OFFSET ?"
)
GET_SUBSCRIPTION = "SELECT * FROM newsletter_subscriptions WHERE id = ?"
GET_SUBSCRIPTION_BY_EMAIL = "SELECT * FROM newsletter_subscriptions WHERE email = ?"
INSERT_SUBSCRIPTION = """INSERT INTO newsletter_subscriptions
    (id, email, status, source) VALUES (?, ?, ?, ?)"""
UPDATE_SUBSCRIPTION_STATUS = """UPDATE newsletter_subscriptions SET
    status=?, unsubscribed_at=CASE WHEN ?='unsubscribed' THEN strftime('%Y-%m-%dT%H:%M:%fZ','now') ELSE unsubscribed_at END,
    updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?"""
DELETE_SUBSCRIPTION = "DELETE FROM newsletter_subscriptions WHERE id = ?"

# ── Publication Issues ───────────────────────────────────────
LIST_PUB_ISSUES = (
    "SELECT * FROM publication_issues ORDER BY created_at DESC LIMIT ? OFFSET ?"
)
LIST_PUB_ISSUES_BY_TYPE = "SELECT * FROM publication_issues WHERE issue_type = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
GET_PUB_ISSUE = "SELECT * FROM publication_issues WHERE id = ?"
INSERT_PUB_ISSUE = """INSERT INTO publication_issues
    (id, issue_type, title, slug, period_start, period_end, status,
     editorial_preface, toc_json, cover_article_id, created_by_user_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
UPDATE_PUB_ISSUE = """UPDATE publication_issues SET
    title=?, editorial_preface=?, toc_json=?, status=?,
    total_pages=?, pdf_r2_key=?, pdf_url=?,
    updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?"""
APPROVE_PUB_ISSUE = """UPDATE publication_issues SET
    status='approved', approved_by_user_id=?, approved_at=strftime('%Y-%m-%dT%H:%M:%fZ','now'),
    updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?"""
PUBLISH_PUB_ISSUE = """UPDATE publication_issues SET
    status='published', published_at=strftime('%Y-%m-%dT%H:%M:%fZ','now'),
    updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?"""
DELETE_PUB_ISSUE = "DELETE FROM publication_issues WHERE id = ?"

# ── Publication Issue Items ──────────────────────────────────
LIST_PUB_ITEMS = (
    "SELECT * FROM publication_issue_items WHERE issue_id = ? ORDER BY position"
)
GET_PUB_ITEM = "SELECT * FROM publication_issue_items WHERE id = ?"
INSERT_PUB_ITEM = """INSERT INTO publication_issue_items
    (id, issue_id, article_id, section, position, item_type, title, excerpt, include_full_content)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
UPDATE_PUB_ITEM = """UPDATE publication_issue_items SET
    section=?, position=?, item_type=?, title=?, excerpt=?, include_full_content=? WHERE id=?"""
DELETE_PUB_ITEM = "DELETE FROM publication_issue_items WHERE id = ?"

# ── Generation Runs ──────────────────────────────────────────
LIST_GEN_RUNS = "SELECT * FROM publication_generation_runs WHERE issue_id = ? ORDER BY created_at DESC"
GET_GEN_RUN = "SELECT * FROM publication_generation_runs WHERE id = ?"
INSERT_GEN_RUN = """INSERT INTO publication_generation_runs
    (id, issue_id, job_name, trigger_source, status) VALUES (?, ?, ?, ?, ?)"""
UPDATE_GEN_RUN = """UPDATE publication_generation_runs SET
    status=?, finished_at=CASE WHEN ? IN ('completed','failed') THEN strftime('%Y-%m-%dT%H:%M:%fZ','now') ELSE finished_at END,
    error_text=?, metrics_json=? WHERE id=?"""

# ── Deliveries ───────────────────────────────────────────────
LIST_DELIVERIES = "SELECT * FROM publication_deliveries WHERE issue_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
GET_DELIVERY = "SELECT * FROM publication_deliveries WHERE id = ?"
INSERT_DELIVERY = """INSERT INTO publication_deliveries
    (id, issue_id, email, channel, status) VALUES (?, ?, ?, ?, ?)"""
UPDATE_DELIVERY_STATUS = """UPDATE publication_deliveries SET
    status=?, provider=?, provider_message_id=?, error_text=?,
    sent_at=CASE WHEN ?='sent' THEN strftime('%Y-%m-%dT%H:%M:%fZ','now') ELSE sent_at END,
    last_attempt_at=strftime('%Y-%m-%dT%H:%M:%fZ','now'),
    attempt_count=attempt_count+1,
    updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?"""
