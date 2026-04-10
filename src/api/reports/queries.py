INSERT_REPORT = (
    "INSERT INTO content_reports"
    " (id, reporter_id, org_id, resource_type, resource_id, reason, detail_text)"
    " VALUES (?, ?, NULLIF(?, ''), ?, ?, ?, NULLIF(?, ''))"
)

SELECT_BY_ID = "SELECT * FROM content_reports WHERE id = ?"

SELECT_ALL = (
    "SELECT * FROM content_reports" " ORDER BY created_at DESC" " LIMIT ? OFFSET ?"
)

SELECT_BY_STATUS = (
    "SELECT * FROM content_reports"
    " WHERE status = ?"
    " ORDER BY created_at ASC"
    " LIMIT ? OFFSET ?"
)

COUNT_ALL = "SELECT COUNT(*) AS c FROM content_reports"

COUNT_BY_STATUS = "SELECT COUNT(*) AS c FROM content_reports WHERE status = ?"

UPDATE_REVIEW = (
    "UPDATE content_reports"
    " SET status = ?, reviewed_by = ?, reviewed_at = datetime('now'),"
    "     action_taken = NULLIF(?, ''), action_note = NULLIF(?, ''),"
    "     updated_at = datetime('now')"
    " WHERE id = ?"
)

CHECK_DUPLICATE = (
    "SELECT id FROM content_reports"
    " WHERE reporter_id = ? AND resource_type = ? AND resource_id = ?"
)
