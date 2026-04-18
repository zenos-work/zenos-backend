import types

import pytest

from api.organizations import service as organization_service_module
from api.organizations.repository import OrganizationRepository
from api.organizations.service import OrganizationService


class _Env:
    DB = object()


class Obj(types.SimpleNamespace):
    def to_dict(self, scope=None):
        data = dict(self.__dict__)
        if scope is not None:
            data["scope"] = scope
        return data


class RepoStub:
    def __init__(self):
        self.orgs = {}
        self.members = {}
        self.teams = {}
        self.team_members = set()
        self.invitations = {}

    async def create_org(self, org_id, name, slug, description, created_by):
        self.orgs[org_id] = Obj(
            id=org_id,
            name=name,
            slug=slug,
            description=description,
            created_by=created_by,
        )

    async def find_org_by_id(self, org_id):
        return self.orgs.get(org_id)

    async def find_orgs_by_user(self, user_id, _limit, _offset):
        if any(oid == user_id for oid in self.orgs):
            return []
        return list(self.orgs.values())

    async def count_orgs_by_user(self, _user_id):
        return len(self.orgs)

    async def find_member(self, org_id, user_id):
        return self.members.get((org_id, user_id))

    async def add_member(self, member_id, org_id, user_id, role, invited_by=None):
        self.members[(org_id, user_id)] = Obj(
            id=member_id,
            org_id=org_id,
            user_id=user_id,
            org_role=role,
            invited_by=invited_by,
        )

    async def update_org(self, org_id, name, description, logo_url, website):
        org = self.orgs[org_id]
        org.name = name
        org.description = description
        org.logo_url = logo_url
        org.website = website

    async def find_members(self, org_id, _limit, _offset):
        return [m for (oid, _), m in self.members.items() if oid == org_id]

    async def count_members(self, org_id):
        return len([1 for (oid, _) in self.members if oid == org_id])

    async def update_member_role(self, org_id, user_id, role):
        self.members[(org_id, user_id)].org_role = role

    async def remove_member(self, org_id, user_id):
        self.members.pop((org_id, user_id), None)

    async def create_team(self, team_id, org_id, name, description, created_by):
        self.teams[team_id] = Obj(
            id=team_id,
            org_id=org_id,
            name=name,
            description=description,
            created_by=created_by,
        )

    async def find_teams(self, org_id, _limit, _offset):
        return [t for t in self.teams.values() if t.org_id == org_id]

    async def count_teams(self, org_id):
        return len([1 for t in self.teams.values() if t.org_id == org_id])

    async def add_team_member(self, team_id, user_id):
        self.team_members.add((team_id, user_id))

    async def remove_team_member(self, team_id, user_id):
        self.team_members.discard((team_id, user_id))

    async def create_invitation(
        self, inv_id, org_id, email, role, token, invited_by, expires_at
    ):
        self.invitations[token] = Obj(
            id=inv_id,
            org_id=org_id,
            email=email,
            org_role=role,
            token=token,
            invited_by=invited_by,
            expires_at=expires_at,
        )

    async def find_invitation_by_token(self, token):
        return self.invitations.get(token)

    async def accept_invitation(self, inv_id):
        for token, inv in list(self.invitations.items()):
            if inv.id == inv_id:
                del self.invitations[token]
                break

    async def delete_invitation(self, inv_id, org_id):
        for token, inv in list(self.invitations.items()):
            if inv.id == inv_id and inv.org_id == org_id:
                del self.invitations[token]
                break

    async def find_invitations(self, org_id, _limit, _offset):
        return [inv for inv in self.invitations.values() if inv.org_id == org_id]

    async def count_invitations(self, org_id):
        return len([1 for inv in self.invitations.values() if inv.org_id == org_id])


@pytest.fixture
def org_service(monkeypatch):
    service = OrganizationService(_Env())
    service._repo = RepoStub()

    id_seq = iter(["org-1", "member-1", "member-2", "team-1", "inv-1", "member-3"])
    monkeypatch.setattr(organization_service_module, "new_id", lambda: next(id_seq))
    monkeypatch.setattr(
        organization_service_module.secrets,
        "token_urlsafe",
        lambda _n: "invite-token",
    )
    return service


@pytest.mark.asyncio
async def test_organization_crud_and_members(org_service):
    created = await org_service.create_org("owner-1", "Acme", "Desc")
    assert created["id"] == "org-1"

    listed = await org_service.list_user_orgs("owner-1", page=1, limit=10)
    assert listed["pagination"]["total"] == 1

    read = await org_service.get_org("org-1", "owner-1")
    assert read["name"] == "Acme"

    updated = await org_service.update_org("org-1", "owner-1", "Acme 2")
    assert updated["name"] == "Acme 2"

    added = await org_service.add_member("org-1", "owner-1", "user-2", role="member")
    assert added["id"] == "member-2"

    with pytest.raises(ValueError, match="already a member"):
        await org_service.add_member("org-1", "owner-1", "user-2", role="member")

    with pytest.raises(ValueError, match="Invalid role"):
        await org_service.add_member("org-1", "owner-1", "user-3", role="invalid")

    role_updated = await org_service.update_member_role(
        "org-1", "owner-1", "user-2", "editor"
    )
    assert role_updated["org_role"] == "editor"

    with pytest.raises(ValueError, match="Member not found"):
        await org_service.update_member_role("org-1", "owner-1", "missing", "viewer")

    with pytest.raises(ValueError, match="Cannot remove the owner"):
        await org_service.remove_member("org-1", "owner-1", "owner-1")

    await org_service.remove_member("org-1", "owner-1", "user-2")

    members = await org_service.list_members("org-1", "owner-1")
    assert len(members["members"]) == 1


@pytest.mark.asyncio
async def test_teams_and_invitations_and_permissions(org_service):
    await org_service.create_org("owner-1", "Beta", "")

    with pytest.raises(PermissionError, match="Admin access required"):
        await org_service.create_team("org-1", "non-admin", "Core")

    team = await org_service.create_team("org-1", "owner-1", "Core", "Core team")
    assert team["id"]

    teams = await org_service.list_teams("org-1", "owner-1")
    assert teams["teams"][0]["name"] == "Core"

    added = await org_service.add_team_member("org-1", "owner-1", "team-1", "user-3")
    assert added["team_id"] == "team-1"

    await org_service.remove_team_member("org-1", "owner-1", "team-1", "user-3")

    invitation = await org_service.create_invitation(
        "org-1", "owner-1", "new@example.com", role="member"
    )
    assert invitation["token"] == "invite-token"

    with pytest.raises(ValueError, match="Invitation not found or expired"):
        await org_service.accept_invitation("missing", "user-4")

    accepted = await org_service.accept_invitation("invite-token", "user-4")
    assert accepted["org_id"] == "org-1"

    inv2 = await org_service.create_invitation("org-1", "owner-1", "x@example.com")
    await org_service.delete_invitation("org-1", "owner-1", inv2["id"])

    inv_list = await org_service.list_invitations("org-1", "owner-1")
    assert inv_list["pagination"]["total"] == 0

    with pytest.raises(ValueError, match="Invalid role"):
        await org_service.create_invitation(
            "org-1", "owner-1", "bad@example.com", role="nope"
        )

    with pytest.raises(PermissionError, match="Not a member"):
        await org_service.get_org("org-1", "outsider")

    with pytest.raises(PermissionError, match="Not a member"):
        await org_service.get_org("missing", "owner-1")


@pytest.mark.asyncio
async def test_accept_invitation_duplicate_member_and_update_missing(org_service):
    await org_service.create_org("owner-1", "Gamma", "")

    await org_service.create_invitation("org-1", "owner-1", "dup@example.com")
    with pytest.raises(ValueError, match="Already a member"):
        await org_service.accept_invitation("invite-token", "owner-1")

    org_service._repo.members[("missing", "owner-1")] = Obj(
        id="m-x",
        org_id="missing",
        user_id="owner-1",
        org_role="owner",
    )
    with pytest.raises(ValueError, match="Organization not found"):
        await org_service.update_org("missing", "owner-1", "N/A")


@pytest.mark.asyncio
async def test_organization_repository_methods(monkeypatch):
    repo = OrganizationRepository(db=object())

    execute_calls = []
    find_one_calls = []
    find_all_calls = []

    async def _execute(sql, *params):
        execute_calls.append((sql, params))

    async def _find_one(sql, *params):
        find_one_calls.append((sql, params))
        return {"id": "x", "c": 3}

    async def _find_all(sql, *params):
        find_all_calls.append((sql, params))
        return [{"id": "x"}, {"id": "y"}]

    monkeypatch.setattr(repo, "execute", _execute)
    monkeypatch.setattr(repo, "find_one", _find_one)
    monkeypatch.setattr(repo, "find_all", _find_all)
    monkeypatch.setattr(repo, "map_one", lambda row, _model: row)
    monkeypatch.setattr(repo, "map_many", lambda rows, _model: rows)

    await repo.create_org("org-1", "Acme", "acme", "", "u1")
    assert await repo.find_org_by_id("org-1") == {"id": "x", "c": 3}
    assert await repo.find_org_by_slug("acme") == {"id": "x", "c": 3}
    assert await repo.find_orgs_by_user("u1", 20, 0) == [{"id": "x"}, {"id": "y"}]
    assert await repo.count_orgs_by_user("u1") == 3
    await repo.update_org("org-1", "Acme 2", "", None, None)

    await repo.add_member("m-1", "org-1", "u2", "member")
    assert await repo.find_members("org-1", 20, 0) == [{"id": "x"}, {"id": "y"}]
    assert await repo.count_members("org-1") == 3
    assert await repo.find_member("org-1", "u2") == {"id": "x", "c": 3}
    await repo.update_member_role("org-1", "u2", "admin")
    await repo.remove_member("org-1", "u2")

    await repo.create_team("t-1", "org-1", "core", "", "u1")
    assert await repo.find_teams("org-1", 20, 0) == [{"id": "x"}, {"id": "y"}]
    assert await repo.count_teams("org-1") == 3
    await repo.add_team_member("t-1", "u3")
    await repo.remove_team_member("t-1", "u3")
    assert await repo.find_team_members("t-1") == [{"id": "x"}, {"id": "y"}]

    await repo.create_invitation(
        "i-1", "org-1", "a@b.com", "member", "tok", "u1", "never"
    )
    assert await repo.find_invitation_by_token("tok") == {"id": "x", "c": 3}
    assert await repo.find_invitations("org-1", 20, 0) == [{"id": "x"}, {"id": "y"}]
    assert await repo.count_invitations("org-1") == 3
    await repo.accept_invitation("i-1")
    await repo.delete_invitation("i-1", "org-1")

    assert len(execute_calls) == 11
    assert len(find_one_calls) == 8
    assert len(find_all_calls) == 5
