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
