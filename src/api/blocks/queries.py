INSERT_BLOCK = (
    "INSERT INTO user_blocks (blocker_id, blocked_id, block_type, reason)"
    " VALUES (?, ?, ?, NULLIF(?, ''))"
)

DELETE_BLOCK = (
    "DELETE FROM user_blocks"
    " WHERE blocker_id = ? AND blocked_id = ? AND block_type = ?"
)

SELECT_BY_BLOCKER = (
    "SELECT * FROM user_blocks"
    " WHERE blocker_id = ? AND block_type = ?"
    " ORDER BY created_at DESC LIMIT ? OFFSET ?"
)

COUNT_BY_BLOCKER = (
    "SELECT COUNT(*) AS c FROM user_blocks" " WHERE blocker_id = ? AND block_type = ?"
)

SELECT_IS_BLOCKED = (
    "SELECT 1 FROM user_blocks"
    " WHERE blocker_id = ? AND blocked_id = ? AND block_type = ? LIMIT 1"
)

SELECT_BLOCKED_IDS = (
    "SELECT blocked_id FROM user_blocks WHERE blocker_id = ? AND block_type = 'block'"
)
