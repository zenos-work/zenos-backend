import types

import pytest

from api.notification_prefs import service as notification_prefs_service_module
from api.notification_prefs.repository import NotificationPrefRepository
from api.notification_prefs.service import NotificationPrefService


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
def pref_service(monkeypatch):
    svc = NotificationPrefService(_Env())
    repo = RepoDyn()
    svc._repo = repo
    seq = iter([f"id-{i}" for i in range(1, 30)])
    monkeypatch.setattr(notification_prefs_service_module, "new_id", lambda: next(seq))
    return svc, repo


@pytest.mark.asyncio
async def test_notification_pref_service_paths(pref_service):
    svc, repo = pref_service

    repo.responses["list_prefs"] = [Obj(id="p1")]
    prefs = await svc.list_prefs("u1")
    assert prefs[0]["id"] == "p1"

    upserted = await svc.upsert_pref("u1", "comments", "email", True)
    assert upserted["is_enabled"] is True

    bulk = await svc.bulk_upsert_prefs(
        "u1",
        [
            {"notification_type": "likes", "channel": "email"},
            {"notification_type": "mentions", "channel": "push", "is_enabled": False},
        ],
    )
    assert len(bulk) == 2

    await svc.delete_pref("u1", "likes", "email")

    repo.responses["list_push_subs"] = [Obj(id="s1")]
    subs = await svc.list_push_subs("u1")
    assert subs[0]["id"] == "s1"

    repo.responses["get_push_sub_by_endpoint"] = None
    created = await svc.subscribe("u1", "web", "https://endpoint", "p", "a", "laptop")
    assert created["id"] == "id-1"

    repo.responses["get_push_sub_by_endpoint"] = Obj(id="s-existing")
    existing = await svc.subscribe("u1", "web", "https://endpoint", "p", "a")
    assert existing["already_subscribed"] is True

    repo.responses["get_push_sub"] = Obj(id="s1")
    unsub = await svc.unsubscribe("s1")
    assert unsub["deactivated"] is True

    repo.responses["get_push_sub"] = None
    with pytest.raises(ValueError, match="Subscription not found"):
        await svc.unsubscribe("missing")


@pytest.mark.asyncio
async def test_notification_pref_repository_methods(monkeypatch):
    repo = NotificationPrefRepository(db=object())
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

    await repo.list_prefs("u1")
    await repo.get_pref("u1", "likes", "email")
    await repo.upsert_pref("u1", "likes", "email", True)
    await repo.delete_pref("u1", "likes", "email")
    await repo.list_push_subs("u1")
    await repo.get_push_sub("s1")
    await repo.get_push_sub_by_endpoint("u1", "https://endpoint")
    await repo.create_push_sub(
        "s1", "u1", "web", "https://endpoint", "p", "a", "laptop"
    )
    await repo.deactivate_push_sub("s1")
    await repo.delete_push_sub("s1")

    assert len(execute_calls) >= 5
