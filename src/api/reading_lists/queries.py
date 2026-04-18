# ── Reading Lists ──
INSERT_LIST = (
    "INSERT INTO reading_lists"
    " (id, user_id, name, description, cover_image_url, is_public)"
    " VALUES (?, ?, ?, NULLIF(?, ''), NULLIF(?, ''), ?)"
)

SELECT_LISTS_BY_USER = (
    "SELECT * FROM reading_lists"
    " WHERE user_id = ?"
    " ORDER BY is_default DESC, updated_at DESC"
    " LIMIT ? OFFSET ?"
)

COUNT_LISTS_BY_USER = "SELECT COUNT(*) AS c FROM reading_lists WHERE user_id = ?"

SELECT_LIST_BY_ID = "SELECT * FROM reading_lists WHERE id = ?"

UPDATE_LIST = (
    "UPDATE reading_lists"
    " SET name = ?, description = NULLIF(?, ''), cover_image_url = NULLIF(?, ''),"
    "     is_public = ?, updated_at = datetime('now')"
    " WHERE id = ? AND user_id = ?"
)

DELETE_LIST = (
    "DELETE FROM reading_lists WHERE id = ? AND user_id = ? AND is_default = 0"
)

# ── Reading List Items ──
INSERT_ITEM = (
    "INSERT INTO reading_list_items"
    " (id, list_id, article_id, note, sort_order)"
    " VALUES (?, ?, ?, NULLIF(?, ''), ?)"
)

SELECT_ITEMS_BY_LIST = (
    "SELECT * FROM reading_list_items"
    " WHERE list_id = ?"
    " ORDER BY sort_order ASC, added_at DESC"
)

COUNT_ITEMS_BY_LIST = "SELECT COUNT(*) AS c FROM reading_list_items WHERE list_id = ?"

DELETE_ITEM = "DELETE FROM reading_list_items WHERE list_id = ? AND article_id = ?"

SELECT_MAX_SORT_ORDER = (
    "SELECT MAX(sort_order) AS m FROM reading_list_items WHERE list_id = ?"
)
