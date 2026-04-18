from typing import Optional, List
from db.repository import BaseRepository
from api.organizations import queries as Q
from models.organization.model import (
    Organization,
    OrgMember,
    Team,
    TeamMember,
    OrgInvitation,
)
from models.base import row_get


class OrganizationRepository(BaseRepository):
    # ── Org CRUD ───────────────────────────────────────────────────────────
    async def create_org(self, org_id, name, slug, description, created_by):
        await self.execute(
            Q.INSERT_ORG, org_id, name, slug, description or "", created_by
        )

    async def find_org_by_id(self, org_id) -> Optional[Organization]:
        row = await self.find_one(Q.SELECT_ORG_BY_ID, org_id)
        return self.map_one(row, Organization)

    async def find_org_by_slug(self, slug) -> Optional[Organization]:
        row = await self.find_one(Q.SELECT_ORG_BY_SLUG, slug)
        return self.map_one(row, Organization)

    async def find_orgs_by_user(self, user_id, limit, offset) -> List[Organization]:
        rows = await self.find_all(Q.SELECT_ORGS_BY_USER, user_id, limit, offset)
        return self.map_many(rows, Organization)

    async def count_orgs_by_user(self, user_id) -> int:
        row = await self.find_one(Q.COUNT_ORGS_BY_USER, user_id)
        return row_get(row, "c", 0)

    async def update_org(self, org_id, name, description, logo_url, website):
        await self.execute(
            Q.UPDATE_ORG, name, description or "", logo_url or "", website or "", org_id
        )

    # ── Members ────────────────────────────────────────────────────────────
    async def add_member(self, member_id, org_id, user_id, role, invited_by=None):
        await self.execute(
            Q.INSERT_MEMBER, member_id, org_id, user_id, role, invited_by or ""
        )

    async def find_members(self, org_id, limit, offset) -> List[OrgMember]:
        rows = await self.find_all(Q.SELECT_MEMBERS, org_id, limit, offset)
        return self.map_many(rows, OrgMember)

    async def count_members(self, org_id) -> int:
        row = await self.find_one(Q.COUNT_MEMBERS, org_id)
        return row_get(row, "c", 0)

    async def find_member(self, org_id, user_id) -> Optional[OrgMember]:
        row = await self.find_one(Q.SELECT_MEMBER, org_id, user_id)
        return self.map_one(row, OrgMember)

    async def update_member_role(self, org_id, user_id, role):
        await self.execute(Q.UPDATE_MEMBER_ROLE, role, org_id, user_id)

    async def remove_member(self, org_id, user_id):
        await self.execute(Q.DELETE_MEMBER, org_id, user_id)

    # ── Teams ──────────────────────────────────────────────────────────────
    async def create_team(self, team_id, org_id, name, description, created_by):
        await self.execute(
            Q.INSERT_TEAM, team_id, org_id, name, description or "", created_by
        )

    async def find_teams(self, org_id, limit, offset) -> List[Team]:
        rows = await self.find_all(Q.SELECT_TEAMS, org_id, limit, offset)
        return self.map_many(rows, Team)

    async def count_teams(self, org_id) -> int:
        row = await self.find_one(Q.COUNT_TEAMS, org_id)
        return row_get(row, "c", 0)

    async def add_team_member(self, team_id, user_id):
        await self.execute(Q.INSERT_TEAM_MEMBER, team_id, user_id)

    async def remove_team_member(self, team_id, user_id):
        await self.execute(Q.DELETE_TEAM_MEMBER, team_id, user_id)

    async def find_team_members(self, team_id) -> List[TeamMember]:
        rows = await self.find_all(Q.SELECT_TEAM_MEMBERS, team_id)
        return self.map_many(rows, TeamMember)

    # ── Invitations ────────────────────────────────────────────────────────
    async def create_invitation(
        self, inv_id, org_id, email, role, token, invited_by, expires_at
    ):
        await self.execute(
            Q.INSERT_INVITATION,
            inv_id,
            org_id,
            email,
            role,
            token,
            invited_by,
            expires_at,
        )

    async def find_invitation_by_token(self, token) -> Optional[OrgInvitation]:
        row = await self.find_one(Q.SELECT_INVITATION_BY_TOKEN, token)
        return self.map_one(row, OrgInvitation)

    async def find_invitations(self, org_id, limit, offset) -> List[OrgInvitation]:
        rows = await self.find_all(Q.SELECT_INVITATIONS_BY_ORG, org_id, limit, offset)
        return self.map_many(rows, OrgInvitation)

    async def count_invitations(self, org_id) -> int:
        row = await self.find_one(Q.COUNT_INVITATIONS_BY_ORG, org_id)
        return row_get(row, "c", 0)

    async def accept_invitation(self, inv_id):
        await self.execute(Q.ACCEPT_INVITATION, inv_id)

    async def delete_invitation(self, inv_id, org_id):
        await self.execute(Q.DELETE_INVITATION, inv_id, org_id)
