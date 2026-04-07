import importlib

import pytest


handler = importlib.import_module("api.tags.handler")
Tag = importlib.import_module("models.tag.model").Tag
TagCreateRequest = importlib.import_module("models.tag.requests").TagCreateRequest
TagService = importlib.import_module("api.tags.service").TagService
TagRepository = importlib.import_module("api.tags.repository").TagRepository
Q = importlib.import_module("api.tags.queries")


class _Req:
    def __init__(self, method, path, body=None):
        self.method = method
        self.url = f"https://test.local{path}"
        self.headers = {}
        self._body = body

    async def json(self):
        return self._body if self._body is not None else {}


class _TagSvc:
    async def list_all(self):
        return [Tag(id="t1", name="Finance", slug="finance")]

    async def list_onboarding(self):
        return [
            Tag(
                id="t2",
                name="Foundations",
                slug="foundations",
                is_onboarding_category=1,
            )
        ]

    async def get_by_slug_or_id(self, identifier):
        if identifier == "missing":
            return None
        return Tag(id="t3", name="Growth", slug="growth")

    async def create(self, req):
        return Tag(
            id="new-tag",
            name=req.name,
            slug=req.name.lower().replace(" ", "-"),
            tag_type=req.tag_type,
            category_slug=req.category_slug,
            is_onboarding_category=req.is_onboarding_category,
        )


class _Env:
    DB = object()


@pytest.fixture
def patch_handler(monkeypatch):
    svc = _TagSvc()
    monkeypatch.setattr(handler, "TagService", lambda env, ctx: svc)
    return svc


async def _dispatch(
    monkeypatch, method, path, *, body=None, user=None, role_ok=True, query=None
):
    async def _get_user(_request, _env):
        return user

    monkeypatch.setattr(handler, "get_user", _get_user)
    monkeypatch.setattr(handler, "require_role", lambda _user, _roles: role_ok)

    return await handler.handle_tags(
        _Req(method, path, body=body),
        _Env(),
        path,
        method,
        query or {},
        object(),
    )


@pytest.mark.asyncio
async def test_tags_handler_get_paths(monkeypatch, patch_handler):
    all_tags = await _dispatch(monkeypatch, "GET", "/api/tags")
    assert all_tags.status_code == 200
    assert all_tags.json()["tags"][0]["slug"] == "finance"

    onboarding_tags = await _dispatch(
        monkeypatch,
        "GET",
        "/api/tags?onboarding=true",
        query={"onboarding": ["true"]},
    )
    assert onboarding_tags.status_code == 200
    assert onboarding_tags.json()["tags"][0]["is_onboarding_category"] == 1

    found = await _dispatch(monkeypatch, "GET", "/api/tags/growth")
    assert found.status_code == 200

    missing = await _dispatch(monkeypatch, "GET", "/api/tags/missing")
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_tags_handler_post_paths(monkeypatch, patch_handler):
    unauth = await _dispatch(
        monkeypatch,
        "POST",
        "/api/tags",
        body={"name": "Alpha"},
        user=None,
    )
    assert unauth.status_code == 401

    forbidden_write = await _dispatch(
        monkeypatch,
        "POST",
        "/api/tags",
        body={"name": "Alpha"},
        user={"sub": "u1", "role": "READER"},
        role_ok=False,
    )
    assert forbidden_write.status_code == 403

    bad_payload = await _dispatch(
        monkeypatch,
        "POST",
        "/api/tags",
        body={"name": ""},
        user={"sub": "u1", "role": "AUTHOR"},
        role_ok=True,
    )
    assert bad_payload.status_code == 422

    restricted_forbidden = await _dispatch(
        monkeypatch,
        "POST",
        "/api/tags",
        body={"name": "Alpha", "is_onboarding_category": True},
        user={"sub": "u1", "role": "AUTHOR"},
        role_ok=False,
    )
    assert restricted_forbidden.status_code == 403

    created = await _dispatch(
        monkeypatch,
        "POST",
        "/api/tags",
        body={"name": "Growth", "tag_type": "topic"},
        user={"sub": "u1", "role": "AUTHOR"},
        role_ok=True,
    )
    assert created.status_code == 201


@pytest.mark.asyncio
async def test_tag_service_create_slugifies(monkeypatch):
    service = TagService(_Env())

    class _Repo:
        def __init__(self):
            self.insert_calls = []

        async def insert(self, *args):
            self.insert_calls.append(args)

    repo = _Repo()
    service._repo = repo

    req = TagCreateRequest(name="Growth Hacking", tag_type="outcome")
    tag = await service.create(req)

    assert tag.slug == "growth-hacking"
    assert repo.insert_calls[0][2] == "growth-hacking"


@pytest.mark.asyncio
async def test_tag_repository_methods(monkeypatch):
    repo = TagRepository(None)

    async def _find_all(sql, *params):
        if sql == Q.SELECT_ALL_WITH_COUNT:
            return [{"id": "t1", "name": "A", "slug": "a"}]
        return [{"id": "t2", "name": "B", "slug": "b", "is_onboarding_category": 1}]

    async def _find_one(sql, *params):
        return {"id": "t3", "name": "C", "slug": "c"}

    executed = []

    async def _execute(sql, *params):
        executed.append((sql, params))

    repo.find_all = _find_all
    repo.find_one = _find_one
    repo.execute = _execute

    all_tags = await repo.find_all_with_count()
    onboarding_tags = await repo.find_onboarding_with_count()
    one_tag = await repo.find_by_slug_or_id("c")
    await repo.insert("tid", "Name", "name", "topic", None, 0)

    assert all_tags[0].slug == "a"
    assert onboarding_tags[0].is_onboarding_category == 1
    assert one_tag.slug == "c"
    assert executed[0][0] == Q.INSERT_TAG
