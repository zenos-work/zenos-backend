from api.organizations.repository import OrganizationRepository
from utils.helpers import new_id, paginate, unique_slug
import secrets


VALID_ROLES = ("owner", "admin", "editor", "member", "viewer")
ADMIN_ROLES = ("owner", "admin")


class OrganizationService:
    def __init__(self, env, ctx=None):
        self._repo = OrganizationRepository(env.DB, ctx)

    # ── Org CRUD ───────────────────────────────────────────────────────────
    async def create_org(self, user_id, name, description=None):
        slug = unique_slug(name)
        org_id = new_id()
        await self._repo.create_org(org_id, name, slug, description, user_id)
        member_id = new_id()
        await self._repo.add_member(member_id, org_id, user_id, "owner")
        org = await self._repo.find_org_by_id(org_id)
        return org.to_dict() if org else {"id": org_id}

    async def list_user_orgs(self, user_id, page=1, limit=20):
        _limit, offset = paginate(page, limit)
        orgs = await self._repo.find_orgs_by_user(user_id, _limit, offset)
        total = await self._repo.count_orgs_by_user(user_id)
        return {
            "organizations": [o.to_dict() for o in orgs],
            "pagination": {
                "page": page,
                "limit": _limit,
                "total": total,
                "pages": (total + _limit - 1) // _limit if _limit else 0,
            },
        }

    async def get_org(self, org_id, user_id):
        member = await self._repo.find_member(org_id, user_id)
        if not member:
            raise PermissionError("Not a member")
        org = await self._repo.find_org_by_id(org_id)
        if not org:
            raise ValueError("Organization not found")
        return org.to_dict()

    async def update_org(
        self, org_id, user_id, name, description=None, logo_url=None, website=None
    ):
        await self._require_admin(org_id, user_id)
        org = await self._repo.find_org_by_id(org_id)
        if not org:
            raise ValueError("Organization not found")
        await self._repo.update_org(
            org_id, name or org.name, description, logo_url, website
        )
        updated = await self._repo.find_org_by_id(org_id)
        return updated.to_dict() if updated else {}

    # ── Members ────────────────────────────────────────────────────────────
    async def list_members(self, org_id, user_id, page=1, limit=20):
        await self._require_member(org_id, user_id)
        _limit, offset = paginate(page, limit)
        members = await self._repo.find_members(org_id, _limit, offset)
        total = await self._repo.count_members(org_id)
        return {
            "members": [m.to_dict() for m in members],
            "pagination": {
                "page": page,
                "limit": _limit,
                "total": total,
                "pages": (total + _limit - 1) // _limit if _limit else 0,
            },
        }

    async def add_member(self, org_id, actor_id, target_user_id, role="member"):
        await self._require_admin(org_id, actor_id)
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role: {role}")
        existing = await self._repo.find_member(org_id, target_user_id)
        if existing:
            raise ValueError("User is already a member")
        mid = new_id()
        await self._repo.add_member(mid, org_id, target_user_id, role, actor_id)
        return {
            "id": mid,
            "org_id": org_id,
            "user_id": target_user_id,
            "org_role": role,
        }

    async def update_member_role(self, org_id, actor_id, target_user_id, role):
        await self._require_admin(org_id, actor_id)
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role: {role}")
        member = await self._repo.find_member(org_id, target_user_id)
        if not member:
            raise ValueError("Member not found")
        await self._repo.update_member_role(org_id, target_user_id, role)
        return {"org_id": org_id, "user_id": target_user_id, "org_role": role}

    async def remove_member(self, org_id, actor_id, target_user_id):
        await self._require_admin(org_id, actor_id)
        member = await self._repo.find_member(org_id, target_user_id)
        if not member:
            raise ValueError("Member not found")
        if member.org_role == "owner":
            raise ValueError("Cannot remove the owner")
        await self._repo.remove_member(org_id, target_user_id)

    # ── Teams ──────────────────────────────────────────────────────────────
    async def create_team(self, org_id, actor_id, name, description=None):
        await self._require_admin(org_id, actor_id)
        tid = new_id()
        await self._repo.create_team(tid, org_id, name, description, actor_id)
        return {"id": tid, "org_id": org_id, "name": name}

    async def list_teams(self, org_id, user_id, page=1, limit=20):
        await self._require_member(org_id, user_id)
        _limit, offset = paginate(page, limit)
        teams = await self._repo.find_teams(org_id, _limit, offset)
        total = await self._repo.count_teams(org_id)
        return {
            "teams": [t.to_dict() for t in teams],
            "pagination": {
                "page": page,
                "limit": _limit,
                "total": total,
                "pages": (total + _limit - 1) // _limit if _limit else 0,
            },
        }

    async def add_team_member(self, org_id, actor_id, team_id, user_id):
        await self._require_admin(org_id, actor_id)
        await self._repo.add_team_member(team_id, user_id)
        return {"team_id": team_id, "user_id": user_id}

    async def remove_team_member(self, org_id, actor_id, team_id, user_id):
        await self._require_admin(org_id, actor_id)
        await self._repo.remove_team_member(team_id, user_id)

    # ── Invitations ────────────────────────────────────────────────────────
    async def create_invitation(self, org_id, actor_id, email, role="member"):
        await self._require_admin(org_id, actor_id)
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role: {role}")
        inv_id = new_id()
        token = secrets.token_urlsafe(32)
        expires_at = "2099-12-31T23:59:59Z"
        await self._repo.create_invitation(
            inv_id, org_id, email, role, token, actor_id, expires_at
        )
        return {"id": inv_id, "token": token, "email": email, "org_role": role}

    async def accept_invitation(self, token, user_id):
        inv = await self._repo.find_invitation_by_token(token)
        if not inv:
            raise ValueError("Invitation not found or expired")
        existing = await self._repo.find_member(inv.org_id, user_id)
        if existing:
            raise ValueError("Already a member")
        mid = new_id()
        await self._repo.add_member(
            mid, inv.org_id, user_id, inv.org_role, inv.invited_by
        )
        await self._repo.accept_invitation(inv.id)
        return {"org_id": inv.org_id, "org_role": inv.org_role}

    async def delete_invitation(self, org_id, actor_id, inv_id):
        await self._require_admin(org_id, actor_id)
        await self._repo.delete_invitation(inv_id, org_id)

    async def list_invitations(self, org_id, actor_id, page=1, limit=20):
        await self._require_admin(org_id, actor_id)
        _limit, offset = paginate(page, limit)
        invs = await self._repo.find_invitations(org_id, _limit, offset)
        total = await self._repo.count_invitations(org_id)
        return {
            "invitations": [i.to_dict(scope="admin") for i in invs],
            "pagination": {
                "page": page,
                "limit": _limit,
                "total": total,
                "pages": (total + _limit - 1) // _limit if _limit else 0,
            },
        }

    # ── Helpers ────────────────────────────────────────────────────────────
    async def _require_admin(self, org_id, user_id):
        member = await self._repo.find_member(org_id, user_id)
        if not member or member.org_role not in ADMIN_ROLES:
            raise PermissionError("Admin access required")

    async def _require_member(self, org_id, user_id):
        member = await self._repo.find_member(org_id, user_id)
        if not member:
            raise PermissionError("Not a member")
