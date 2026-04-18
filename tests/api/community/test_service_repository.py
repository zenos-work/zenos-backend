import types

import pytest

from api.community import service as community_service_module
from api.community.repository import CommunityRepository
from api.community.service import CommunityService


class _Env:
    DB = object()


class Obj(types.SimpleNamespace):
    def to_dict(self, scope=None):
        data = dict(self.__dict__)
        if scope is not None:
            data["scope"] = scope
        return data


class RepoDyn:
    def __init__(self):
        self.responses = {}

    def __getattr__(self, name):
        async def _method(*_args, **_kwargs):
            return self.responses.get(name)

        return _method


@pytest.fixture
def community_service(monkeypatch):
    svc = CommunityService(_Env())
    repo = RepoDyn()
    svc._repo = repo
    seq = iter([f"id-{i}" for i in range(1, 60)])
    monkeypatch.setattr(community_service_module, "new_id", lambda: next(seq))
    return svc, repo


@pytest.mark.asyncio
async def test_community_service_happy_paths(community_service):
    svc, repo = community_service

    repo.responses["list_spaces"] = [Obj(id="s1")]
    repo.responses["list_spaces_public"] = [Obj(id="s2")]
    repo.responses["get_space"] = Obj(
        id="s1",
        name="S",
        description="",
        cover_image_url="",
        icon="",
        space_type="open",
        membership_tier="",
    )
    assert (await svc.list_spaces("o1"))["spaces"][0]["id"] == "s1"
    assert (await svc.list_spaces_public())["spaces"][0]["id"] == "s2"
    assert (await svc.get_space("s1"))["id"] == "s1"
    assert (await svc.create_space("o1", "u1", "S", "s"))["id"] == "id-1"
    assert (await svc.update_space("s1", name="S2"))["id"] == "s1"
    await svc.delete_space("s1")

    repo.responses["list_members"] = [Obj(id="m1")]
    repo.responses["get_member"] = None
    assert (await svc.list_members("s1"))["members"][0]["id"] == "m1"
    assert (await svc.join_space("s1", "u1"))["joined"] is True
    repo.responses["get_member"] = Obj(id="m1", org_role="member")
    assert (await svc.leave_space("s1", "u1"))["left"] is True
    assert (await svc.update_member_role("s1", "u1", "admin"))["updated"] is True

    repo.responses["list_posts"] = [Obj(id="p1")]
    repo.responses["list_replies"] = [Obj(id="p2")]
    repo.responses["get_post"] = Obj(
        id="p1",
        space_id="s1",
        title="T",
        body="B",
        post_type="discussion",
        status="published",
        pinned=False,
    )
    assert (await svc.list_posts("s1"))["posts"][0]["id"] == "p1"
    assert (await svc.list_replies("p1"))["replies"][0]["id"] == "p2"
    assert (await svc.get_post("p1"))["id"] == "p1"
    assert (await svc.create_post("s1", "u1", title="T"))["id"] == "id-2"
    assert (await svc.create_post("s1", "u1", parent_id="p1", title="Reply"))[
        "id"
    ] == "id-3"
    assert (await svc.update_post("p1", title="T2"))["id"] == "p1"
    await svc.delete_post("p1")
    assert (await svc.like_post("p1"))["liked"] is True


@pytest.mark.asyncio
async def test_community_service_not_found(community_service):
    svc, repo = community_service
    repo.responses["get_space"] = None
    with pytest.raises(ValueError, match="Space not found"):
        await svc.get_space("x")
    repo.responses["get_member"] = Obj(id="m1")
    with pytest.raises(ValueError, match="Already a member"):
        await svc.join_space("s1", "u1")
    repo.responses["get_member"] = None
    with pytest.raises(ValueError, match="Not a member"):
        await svc.leave_space("s1", "u1")
    with pytest.raises(ValueError, match="Member not found"):
        await svc.update_member_role("s1", "u1", "admin")
    repo.responses["get_post"] = None
    with pytest.raises(ValueError, match="Post not found"):
        await svc.get_post("x")


@pytest.mark.asyncio
async def test_community_repository_methods(monkeypatch):
    repo = CommunityRepository(db=object())
    execute_calls = []

    async def _execute(sql, *params):
        execute_calls.append((sql, params))

    async def _find_all(sql, *params):
        return [{"id": "x"}, {"id": "y"}]

    async def _find_one(sql, *params):
        return {"id": "x"}

    monkeypatch.setattr(repo, "execute", _execute)
    monkeypatch.setattr(repo, "find_all", _find_all)
    monkeypatch.setattr(repo, "find_one", _find_one)
    monkeypatch.setattr(repo, "map_many", lambda rows, _model: rows)
    monkeypatch.setattr(repo, "map_one", lambda row, _model: row)

    await repo.list_spaces("o1", 20, 0)
    await repo.list_spaces_public(20, 0)
    await repo.get_space("s1")
    await repo.create_space("s1", "o1", "S", "s", "", "", "", "open", "", "u1")
    await repo.update_space("s1", "S", "", "", "", "open", "")
    await repo.delete_space("s1")
    await repo.increment_member_count("s1")
    await repo.decrement_member_count("s1")
    await repo.increment_post_count("s1")
    await repo.decrement_post_count("s1")
    await repo.list_members("s1", 20, 0)
    await repo.get_member("s1", "u1")
    await repo.add_member("s1", "u1")
    await repo.update_member_role("s1", "u1", "admin")
    await repo.remove_member("s1", "u1")
    await repo.list_posts("s1", 20, 0)
    await repo.list_replies("p1", 20, 0)
    await repo.get_post("p1")
    await repo.create_post(
        "p1", "s1", "u1", "", "T", "B", "discussion", "", "published", False
    )
    await repo.update_post("p1", "T", "B", "discussion", "published", False)
    await repo.delete_post("p1")
    await repo.increment_reply_count("p1")
    await repo.increment_like_count("p1")

    assert len(execute_calls) > 10
