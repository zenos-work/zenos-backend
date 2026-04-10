INSERT_ARTICLE_EVENT = (
    "INSERT INTO article_events"
    " (id, article_id, actor_user_id, event_type, event_value, event_source, metadata_json)"
    " VALUES (?, ?, NULLIF(?, ''), ?, ?, ?, NULLIF(?, ''))"
)

UPSERT_HOURLY_SUCCESS = (
    "INSERT INTO article_success_hourly"
    " (article_id, bucket_hour, views_count, likes_count, comments_count, outcome_events_count,"
    "  outcome_tag_count, engagement_score, success_rate, updated_at)"
    " SELECT"
    "   e.article_id,"
    "   ?,"
    "   SUM(CASE WHEN e.event_type = 'VIEW' THEN e.event_value ELSE 0 END) AS views_count,"
    "   SUM(CASE WHEN e.event_type = 'LIKE' THEN e.event_value ELSE 0 END) AS likes_count,"
    "   SUM(CASE WHEN e.event_type = 'COMMENT' THEN e.event_value ELSE 0 END) AS comments_count,"
    "   SUM(CASE WHEN e.event_type = 'OUTCOME' THEN e.event_value ELSE 0 END) AS outcome_events_count,"
    "   COALESCE(ot.outcome_tag_count, 0) AS outcome_tag_count,"
    "   ROUND((SUM(CASE WHEN e.event_type = 'VIEW' THEN e.event_value ELSE 0 END) * 1.0)"
    "     + (SUM(CASE WHEN e.event_type = 'LIKE' THEN e.event_value ELSE 0 END) * 5.0)"
    "     + (SUM(CASE WHEN e.event_type = 'COMMENT' THEN e.event_value ELSE 0 END) * 8.0)"
    "     + (SUM(CASE WHEN e.event_type = 'OUTCOME' THEN e.event_value ELSE 0 END) * 10.0)"
    "     + (COALESCE(ot.outcome_tag_count, 0) * 4.0), 2) AS engagement_score,"
    "   MIN(100.0, ROUND((("
    "     (SUM(CASE WHEN e.event_type = 'VIEW' THEN e.event_value ELSE 0 END) * 1.0)"
    "     + (SUM(CASE WHEN e.event_type = 'LIKE' THEN e.event_value ELSE 0 END) * 5.0)"
    "     + (SUM(CASE WHEN e.event_type = 'COMMENT' THEN e.event_value ELSE 0 END) * 8.0)"
    "     + (SUM(CASE WHEN e.event_type = 'OUTCOME' THEN e.event_value ELSE 0 END) * 10.0)"
    "     + (COALESCE(ot.outcome_tag_count, 0) * 4.0)"
    "   ) / 200.0) * 100.0, 2)) AS success_rate,"
    "   datetime('now')"
    " FROM article_events e"
    " LEFT JOIN ("
    "   SELECT at.article_id, COUNT(*) AS outcome_tag_count"
    "   FROM article_tags at"
    "   JOIN tags t ON t.id = at.tag_id"
    "   WHERE t.tag_type = 'outcome'"
    "   GROUP BY at.article_id"
    " ) ot ON ot.article_id = e.article_id"
    " WHERE e.created_at >= ? AND e.created_at < ?"
    " GROUP BY e.article_id"
    " ON CONFLICT(article_id, bucket_hour) DO UPDATE SET"
    "   views_count = excluded.views_count,"
    "   likes_count = excluded.likes_count,"
    "   comments_count = excluded.comments_count,"
    "   outcome_events_count = excluded.outcome_events_count,"
    "   outcome_tag_count = excluded.outcome_tag_count,"
    "   engagement_score = excluded.engagement_score,"
    "   success_rate = excluded.success_rate,"
    "   updated_at = datetime('now')"
)

COUNT_EVENTS_IN_WINDOW = (
    "SELECT COUNT(*) AS count"
    " FROM article_events"
    " WHERE created_at >= ? AND created_at < ?"
)

# ═══════════════════════════════════════════════════════════════
# Phase 6 Step 26 — Extended analytics queries
# ═══════════════════════════════════════════════════════════════

# ── Analytics Events ─────────────────────────────────────────
LIST_ANALYTICS_EVENTS = """SELECT * FROM analytics_events
  WHERE org_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"""
INSERT_ANALYTICS_EVENT = """INSERT INTO analytics_events
  (id, org_id, user_id, session_id, anonymous_id,
   event_category, event_action, event_label, event_value,
   resource_type, resource_id, page_url, referrer_url,
   utm_source, utm_medium, utm_campaign, properties,
   device_type, country_code)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

# ── Conversion Goals ─────────────────────────────────────────
LIST_GOALS = "SELECT * FROM conversion_goals WHERE org_id = ? ORDER BY created_at DESC"
GET_GOAL = "SELECT * FROM conversion_goals WHERE id = ?"
INSERT_GOAL = """INSERT INTO conversion_goals
  (id, org_id, name, goal_type, target_event_category, target_event_action,
   target_resource_id, value_cents, is_active)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
UPDATE_GOAL = """UPDATE conversion_goals
  SET name = ?, goal_type = ?, target_event_category = ?, target_event_action = ?,
      target_resource_id = ?, value_cents = ?, is_active = ?
  WHERE id = ?"""
DELETE_GOAL = "DELETE FROM conversion_goals WHERE id = ?"

# ── Conversion Events ────────────────────────────────────────
LIST_CONVERSIONS = """SELECT * FROM conversion_events
  WHERE goal_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"""
INSERT_CONVERSION = """INSERT INTO conversion_events
  (id, goal_id, org_id, user_id, anonymous_id, session_id, event_id, value_cents)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""

# ── Funnel Definitions ───────────────────────────────────────
LIST_FUNNELS = (
    "SELECT * FROM funnel_definitions WHERE org_id = ? ORDER BY created_at DESC"
)
GET_FUNNEL = "SELECT * FROM funnel_definitions WHERE id = ?"
INSERT_FUNNEL = """INSERT INTO funnel_definitions
  (id, org_id, name, description, is_active, created_by) VALUES (?, ?, ?, ?, ?, ?)"""
UPDATE_FUNNEL = """UPDATE funnel_definitions
  SET name = ?, description = ?, is_active = ? WHERE id = ?"""
DELETE_FUNNEL = "DELETE FROM funnel_definitions WHERE id = ?"

# ── Funnel Steps ─────────────────────────────────────────────
LIST_FUNNEL_STEPS = (
    "SELECT * FROM funnel_steps WHERE funnel_id = ? ORDER BY step_number"
)
INSERT_FUNNEL_STEP = """INSERT INTO funnel_steps
  (id, funnel_id, step_number, name, event_category, event_action,
   resource_type, resource_id)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
DELETE_FUNNEL_STEP = "DELETE FROM funnel_steps WHERE id = ?"

# ── A/B Experiments ──────────────────────────────────────────
LIST_EXPERIMENTS = (
    "SELECT * FROM ab_experiments WHERE org_id = ? ORDER BY created_at DESC"
)
GET_EXPERIMENT = "SELECT * FROM ab_experiments WHERE id = ?"
INSERT_EXPERIMENT = """INSERT INTO ab_experiments
  (id, org_id, name, hypothesis, status, traffic_split,
   success_goal_id, created_by)
  VALUES (?, ?, ?, ?, 'draft', ?, ?, ?)"""
UPDATE_EXPERIMENT = """UPDATE ab_experiments
  SET name = ?, hypothesis = ?, status = ?, traffic_split = ?,
      started_at = ?, ended_at = ?, winner_variant = ?
  WHERE id = ?"""
DELETE_EXPERIMENT = "DELETE FROM ab_experiments WHERE id = ?"

# ── A/B Experiment Variants ──────────────────────────────────
LIST_VARIANTS = (
    "SELECT * FROM ab_experiment_variants WHERE experiment_id = ? ORDER BY name"
)
GET_VARIANT = "SELECT * FROM ab_experiment_variants WHERE id = ?"
INSERT_VARIANT = """INSERT INTO ab_experiment_variants
  (id, experiment_id, name, description, changes)
  VALUES (?, ?, ?, ?, ?)"""
UPDATE_VARIANT_STATS = """UPDATE ab_experiment_variants
  SET impressions = ?, conversions = ? WHERE id = ?"""
DELETE_VARIANT = "DELETE FROM ab_experiment_variants WHERE id = ?"

# ── A/B Experiment Assignments ───────────────────────────────
GET_ASSIGNMENT = """SELECT variant_id FROM ab_experiment_assignments
  WHERE experiment_id = ? AND anonymous_id = ?"""
INSERT_ASSIGNMENT = """INSERT OR IGNORE INTO ab_experiment_assignments
  (experiment_id, anonymous_id, variant_id) VALUES (?, ?, ?)"""

# ── Metering / Dashboard (Steps 27-28) ──────────────────────
COUNT_EVENTS_BY_CATEGORY = """SELECT event_category, COUNT(*) AS cnt
  FROM analytics_events WHERE org_id = ? AND created_at >= ? AND created_at < ?
  GROUP BY event_category ORDER BY cnt DESC"""
COUNT_CONVERSIONS_BY_GOAL = """SELECT g.name, COUNT(ce.id) AS cnt, SUM(ce.value_cents) AS total_value
  FROM conversion_events ce JOIN conversion_goals g ON g.id = ce.goal_id
  WHERE ce.org_id = ? AND ce.created_at >= ? AND ce.created_at < ?
  GROUP BY ce.goal_id ORDER BY cnt DESC"""
EXPERIMENT_SUMMARY = """SELECT e.id, e.name, e.status,
    v.id AS variant_id, v.name AS variant_name, v.impressions, v.conversions
  FROM ab_experiments e JOIN ab_experiment_variants v ON v.experiment_id = e.id
  WHERE e.org_id = ? ORDER BY e.created_at DESC"""
