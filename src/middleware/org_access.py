"""Org-level access control helpers.

Role hierarchy: owner > admin > editor > member > viewer
"""

ROLE_HIERARCHY = {
    "owner": 4,
    "admin": 3,
    "editor": 2,
    "member": 1,
    "viewer": 0,
}


async def resolve_org_role(db, user_id, org_id):
    """Return the user's org_role string or None if not a member."""
    from db.executor import D1Executor

    ex = D1Executor(db)
    row = await ex.first(
        "SELECT org_role FROM org_members WHERE org_id = ? AND user_id = ?",
        org_id,
        user_id,
    )
    if not row:
        return None
    from models.base import row_get

    return row_get(row, "org_role")


def check_org_role(user_role, min_role):
    """Return True if user_role >= min_role in the hierarchy."""
    if not user_role:
        return False
    return ROLE_HIERARCHY.get(user_role, -1) >= ROLE_HIERARCHY.get(min_role, 99)


async def require_org_role(db, user_id, org_id, min_role):
    """Raise PermissionError if the user lacks the required org role."""
    role = await resolve_org_role(db, user_id, org_id)
    if not check_org_role(role, min_role):
        raise PermissionError(f"Requires org role '{min_role}' or higher")
    return role
