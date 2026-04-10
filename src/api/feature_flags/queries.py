GET_ALL_FLAGS = "SELECT * FROM feature_flags ORDER BY category, name"

GET_ACTIVE_FLAGS = (
    "SELECT * FROM feature_flags WHERE is_active = 1 ORDER BY category, name"
)

GET_FLAG_BY_KEY = "SELECT * FROM feature_flags WHERE flag_key = ?"

GET_FLAG_BY_ID = "SELECT * FROM feature_flags WHERE id = ?"

GET_FLAGS_BY_CATEGORY = "SELECT * FROM feature_flags WHERE category = ? ORDER BY name"

COUNT_ALL = "SELECT COUNT(*) AS c FROM feature_flags"

INSERT_FLAG = (
    "INSERT INTO feature_flags"
    " (id, flag_key, name, description, category, is_active,"
    "  target_type, targets, rollout_pct, metadata, created_by)"
    " VALUES (?, ?, ?, NULLIF(?, ''), ?, ?, ?, ?, ?, ?, ?)"
)

UPDATE_FLAG = (
    "UPDATE feature_flags"
    " SET name = ?, description = NULLIF(?, ''), category = ?,"
    "     is_active = ?, target_type = ?, targets = ?,"
    "     rollout_pct = ?, metadata = ?,"
    "     updated_by = ?, updated_at = datetime('now')"
    " WHERE id = ?"
)

DELETE_FLAG = "DELETE FROM feature_flags WHERE id = ?"

TOGGLE_FLAG = (
    "UPDATE feature_flags"
    " SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END,"
    "     updated_by = ?, updated_at = datetime('now')"
    " WHERE id = ?"
)

LIST_ACTIVE_USER_IDS = "SELECT id FROM users WHERE is_active = 1"

LIST_ACTIVE_USER_IDS_BY_ROLE = (
    "SELECT id FROM users WHERE is_active = 1 AND role IN ({placeholders})"
)

LIST_ACTIVE_USER_IDS_BY_IDS = (
    "SELECT id FROM users WHERE is_active = 1 AND id IN ({placeholders})"
)

LIST_ACTIVE_USER_IDS_BY_MEMBERSHIP_TIERS = (
    "SELECT id FROM users WHERE is_active = 1 AND membership_tier IN ({placeholders})"
)

LIST_ACTIVE_USER_IDS_BY_ORG_IDS = (
    "SELECT DISTINCT u.id"
    " FROM users u"
    " JOIN org_members om ON om.user_id = u.id"
    " WHERE u.is_active = 1 AND om.org_id IN ({placeholders})"
)

LIST_ACTIVE_USER_IDS_BY_ORG_TIERS = (
    "SELECT DISTINCT u.id"
    " FROM users u"
    " JOIN org_members om ON om.user_id = u.id"
    " JOIN organizations o ON o.id = om.org_id"
    " WHERE u.is_active = 1 AND o.plan_tier IN ({placeholders})"
)

LIST_USER_IDS_WITH_ENABLED_PREF = (
    "SELECT user_id FROM notification_preferences"
    " WHERE notification_type = ? AND channel = ? AND is_enabled = 1"
    " AND user_id IN ({placeholders})"
)

LIST_USER_IDS_WITH_ACTIVE_PUSH_SUBS = (
    "SELECT DISTINCT user_id FROM push_subscriptions"
    " WHERE is_active = 1 AND user_id IN ({placeholders})"
)

INSERT_NOTIFICATION = (
    "INSERT INTO notifications"
    " (id, user_id, actor_id, type, article_id, comment_id, message, channel, delivery_status, group_key)"
    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)
