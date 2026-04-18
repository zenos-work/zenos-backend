"""Article security-level enforcement.

Access control matrix:
  public       — everyone
  internal     — any org member (all 5 roles)
  confidential — owner, admin, editor, or article's author_id
  restricted   — explicit workflow_permissions grant, or owner/admin
"""

SECURITY_FILTER_PUBLIC = " AND a.security_level = 'public'"

SECURITY_FILTER_ORG_MEMBER = (
    " AND (a.security_level = 'public'"
    "  OR (a.security_level = 'internal' AND a.org_id = ?)"
    "  OR (a.security_level = 'confidential' AND a.org_id = ?"
    "      AND (a.author_id = ? OR EXISTS ("
    "        SELECT 1 FROM org_members om"
    "        WHERE om.org_id = a.org_id AND om.user_id = ?"
    "        AND om.org_role IN ('owner','admin','editor')"
    "      )))"
    "  OR (a.security_level = 'restricted' AND a.org_id = ?"
    "      AND EXISTS ("
    "        SELECT 1 FROM org_members om"
    "        WHERE om.org_id = a.org_id AND om.user_id = ?"
    "        AND om.org_role IN ('owner','admin')"
    "      ))"
    " )"
)


def security_params_public():
    """No extra params needed for public-only filter."""
    return ()


def security_params_org_member(org_id, user_id):
    """Return parameter tuple for SECURITY_FILTER_ORG_MEMBER."""
    return (org_id, org_id, user_id, user_id, org_id, user_id)


async def can_read_article(db, article_row, user_id=None, org_id=None):
    """Check if a user can read a specific article based on security_level.

    Returns True/False. For use after fetching a single article.
    """
    from models.base import row_get

    level = (
        row_get(article_row, "security_level", "public")
        if not isinstance(article_row, str)
        else article_row
    )

    if level == "public":
        return True

    if not user_id:
        return False

    article_org_id = (
        row_get(article_row, "org_id") if not isinstance(article_row, str) else org_id
    )
    if not article_org_id:
        return level == "public"

    from db.executor import D1Executor

    ex = D1Executor(db)

    if level == "internal":
        row = await ex.first(
            "SELECT 1 AS ok FROM org_members WHERE org_id = ? AND user_id = ?",
            article_org_id,
            user_id,
        )
        return row is not None

    if level == "confidential":
        author_id = (
            row_get(article_row, "author_id")
            if not isinstance(article_row, str)
            else None
        )
        if author_id == user_id:
            return True
        row = await ex.first(
            "SELECT 1 AS ok FROM org_members WHERE org_id = ? AND user_id = ?"
            " AND org_role IN ('owner','admin','editor')",
            article_org_id,
            user_id,
        )
        return row is not None

    if level == "restricted":
        row = await ex.first(
            "SELECT 1 AS ok FROM org_members WHERE org_id = ? AND user_id = ?"
            " AND org_role IN ('owner','admin')",
            article_org_id,
            user_id,
        )
        return row is not None

    return False
