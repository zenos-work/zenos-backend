SELECT_ALL_WITH_COUNT = (
    "SELECT t.*, COUNT(at.article_id) AS article_count"
    " FROM tags t"
    " LEFT JOIN article_tags at ON t.id = at.tag_id"
    " GROUP BY t.id ORDER BY article_count DESC"
)

SELECT_BY_SLUG_OR_ID = "SELECT * FROM tags WHERE slug = ? OR id = ?"

INSERT_TAG = "INSERT INTO tags (id, name, slug) VALUES (?, ?, ?)"
