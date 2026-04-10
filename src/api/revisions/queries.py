SELECT_BY_ARTICLE = (
    "SELECT * FROM article_revisions"
    " WHERE article_id = ?"
    " ORDER BY version_number DESC"
    " LIMIT ? OFFSET ?"
)

COUNT_BY_ARTICLE = "SELECT COUNT(*) AS c FROM article_revisions WHERE article_id = ?"

SELECT_BY_ARTICLE_AND_VERSION = (
    "SELECT * FROM article_revisions" " WHERE article_id = ? AND version_number = ?"
)

SELECT_LATEST_VERSION = (
    "SELECT MAX(version_number) AS v FROM article_revisions WHERE article_id = ?"
)

INSERT_REVISION = (
    "INSERT INTO article_revisions"
    " (id, article_id, version_number, title, subtitle, content,"
    "  cover_image_url, reading_level, tags_snapshot,"
    "  editor_id, change_summary, edit_type, word_count, char_diff)"
    " VALUES (?, ?, ?, ?, NULLIF(?, ''), ?, NULLIF(?, ''), NULLIF(?, ''), ?,"
    "  ?, NULLIF(?, ''), ?, ?, ?)"
)
