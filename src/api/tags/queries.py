SELECT_ALL_WITH_COUNT = (
    "SELECT t.*, COUNT(at.article_id) AS article_count"
    " FROM tags t"
    " LEFT JOIN article_tags at ON t.id = at.tag_id"
    " GROUP BY t.id ORDER BY article_count DESC"
)

SELECT_ONBOARDING_WITH_COUNT = (
    "SELECT t.*, COUNT(at.article_id) AS article_count"
    " FROM tags t"
    " LEFT JOIN article_tags at ON t.id = at.tag_id"
    " WHERE t.tag_type = 'topic'"
    "   AND (COALESCE(t.is_onboarding_category, 0) = 1 OR t.category_slug IS NOT NULL)"
    " GROUP BY t.id"
    " ORDER BY COALESCE(t.is_onboarding_category, 0) DESC,"
    "          COALESCE(t.category_slug, t.slug) ASC,"
    "          article_count DESC,"
    "          t.name ASC"
)

SELECT_BY_SLUG_OR_ID = "SELECT * FROM tags WHERE slug = ? OR id = ?"

INSERT_TAG = (
    "INSERT INTO tags (id, name, slug, tag_type, category_slug, is_onboarding_category)"
    " VALUES (?, ?, ?, ?, ?, ?)"
)
