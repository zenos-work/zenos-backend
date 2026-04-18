"""Series API SQL queries."""

SELECT_SERIES_BY_ID = """
SELECT
  s.id,
  s.author_id,
  s.name,
  s.description,
  s.cover_image_url,
  s.created_at,
  s.updated_at,
  COUNT(asoc.id) as article_count
FROM series s
LEFT JOIN article_series asoc ON s.id = asoc.series_id
WHERE s.id = ?
GROUP BY s.id
"""

SELECT_SERIES_BY_AUTHOR = """
SELECT
  s.id,
  s.author_id,
  s.name,
  s.description,
  s.cover_image_url,
  s.created_at,
  s.updated_at,
  COUNT(asoc.id) as article_count
FROM series s
LEFT JOIN article_series asoc ON s.id = asoc.series_id
WHERE s.author_id = ?
GROUP BY s.id
ORDER BY s.updated_at DESC
LIMIT ? OFFSET ?
"""

SELECT_SERIES_BY_AUTHOR_COUNT = """
SELECT COUNT(*) as total
FROM series
WHERE author_id = ?
"""

SELECT_SERIES_ARTICLES = """
SELECT
  a.id,
  a.title,
  a.slug,
  a.subtitle,
  a.content_type,
  a.status,
  a.author_id,
  a.cover_image_url,
  a.read_time_minutes,
  a.reading_level,
  a.views_count,
  a.likes_count,
  a.dislikes_count,
  a.shares_count,
  a.comments_count,
  a.is_featured,
  a.published_at,
  a.created_at,
  a.moderation_state,
  a.moderation_note,
  a.seo_title,
  a.seo_description,
  a.canonical_url,
  a.og_image_url,
  a.seo_schema_type,
  a.citations,
  a.author_name,
  a.author_avatar,
  a.tags,
  asoc.part_number,
  (SELECT COUNT(*) FROM article_series WHERE series_id = ?) as total_parts
FROM article_series asoc
INNER JOIN articles a ON asoc.article_id = a.id
WHERE asoc.series_id = ?
ORDER BY asoc.part_number ASC
"""

SELECT_ARTICLE_SERIES = """
SELECT
  s.id,
  s.name,
  s.description,
  s.cover_image_url,
  asoc.part_number,
  (SELECT COUNT(*) FROM article_series WHERE series_id = s.id) as total_parts,
  (SELECT group_concat(a2.slug || ':' || as2.part_number) FROM article_series as2 INNER JOIN articles a2 ON as2.article_id = a2.id WHERE as2.series_id = s.id) as all_parts
FROM article_series asoc
INNER JOIN series s ON asoc.series_id = s.id
WHERE asoc.article_id = ?
LIMIT 1
"""

INSERT_SERIES = """
INSERT INTO series (id, author_id, name, description, cover_image_url, created_at, updated_at)
VALUES (?, ?, ?, NULLIF(?, ''), NULLIF(?, ''), ?, ?)
"""

UPDATE_SERIES = """
UPDATE series
SET name = ?,
    description = NULLIF(?, ''),
    cover_image_url = NULLIF(?, ''),
    updated_at = ?
WHERE id = ? AND author_id = ?
"""

INSERT_ARTICLE_SERIES = """
INSERT INTO article_series (id, article_id, series_id, part_number, created_at, updated_at)
VALUES (?, ?, ?, ?, ?, ?)
"""

UPDATE_ARTICLE_SERIES_PART = """
UPDATE article_series
SET part_number = ?, updated_at = ?
WHERE article_id = ? AND series_id = ?
"""

DELETE_ARTICLE_SERIES = """
DELETE FROM article_series
WHERE article_id = ? AND series_id = ?
"""

DELETE_SERIES = """
DELETE FROM series
WHERE id = ? AND author_id = ?
"""

SELECT_SERIES_EXISTS = """
SELECT 1 FROM series WHERE id = ? AND author_id = ?
"""

SELECT_ARTICLE_SERIES_EXISTS = """
SELECT 1 FROM article_series WHERE article_id = ? AND series_id = ?
"""
