# Pure SQL constants — no imports, no functions, no logic.
# Naming convention: VERB_ENTITY_BY_FIELD

# ── Articles FTS ──────────────────────────────────────────────────────────────
# articles_fts stores title, subtitle, content for all articles.
# rank is FTS5's BM25 relevance pseudo-column; lower value = more relevant,
# so ORDER BY rank gives best results first (ascending negative floats).
SELECT_ARTICLES_FTS = (
    "SELECT a.*, u.name AS author_name, u.avatar_url AS author_avatar"
    " FROM articles_fts"
    " JOIN articles a ON a.id = articles_fts.article_id"
    " JOIN users u ON a.author_id = u.id"
    " WHERE articles_fts MATCH ?"
    " AND a.status = 'PUBLISHED'"
    " ORDER BY rank"
    " LIMIT ? OFFSET ?"
)

COUNT_ARTICLES_FTS = (
    "SELECT COUNT(*) AS c"
    " FROM articles_fts"
    " JOIN articles a ON a.id = articles_fts.article_id"
    " WHERE articles_fts MATCH ?"
    " AND a.status = 'PUBLISHED'"
)

# ── Tags ──────────────────────────────────────────────────────────────────────
SELECT_TAGS_SEARCH = (
    "SELECT * FROM tags WHERE name LIKE ? OR slug LIKE ?"
    " ORDER BY name ASC LIMIT ? OFFSET ?"
)

COUNT_TAGS_SEARCH = "SELECT COUNT(*) AS c FROM tags WHERE name LIKE ? OR slug LIKE ?"

# ── Authors (public-facing writer profiles) ───────────────────────────────────
SELECT_AUTHORS_SEARCH = (
    "SELECT * FROM users"
    " WHERE name LIKE ?"
    "   AND role IN ('AUTHOR', 'APPROVER', 'SUPERADMIN')"
    "   AND is_active = 1"
    " ORDER BY name ASC LIMIT ? OFFSET ?"
)

COUNT_AUTHORS_SEARCH = (
    "SELECT COUNT(*) AS c FROM users"
    " WHERE name LIKE ?"
    "   AND role IN ('AUTHOR', 'APPROVER', 'SUPERADMIN')"
    "   AND is_active = 1"
)
