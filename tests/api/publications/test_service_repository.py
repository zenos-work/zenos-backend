import types

import pytest

from api.publications import service as publications_service_module
from api.publications.repository import PublicationRepository
from api.publications.service import PublicationService


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
def publication_service(monkeypatch):
    svc = PublicationService(_Env())
    repo = RepoDyn()
    svc._repo = repo
    seq = iter([f"id-{i}" for i in range(1, 70)])
    monkeypatch.setattr(publications_service_module, "new_id", lambda: next(seq))
    return svc, repo


@pytest.mark.asyncio
async def test_publication_service_happy_paths(publication_service):
    svc, repo = publication_service

    repo.responses["list_subscriptions"] = [Obj(id="s1")]
    repo.responses["get_subscription"] = Obj(id="s1")
    assert (await svc.list_subscriptions())["subscriptions"][0]["id"] == "s1"
    assert (await svc.get_subscription("s1"))["id"] == "s1"
    assert (await svc.create_subscription("a@b.com"))["id"] == "id-1"
    assert (await svc.update_subscription_status("s1", "unsubscribed"))["id"] == "s1"
    await svc.delete_subscription("s1")

    repo.responses["list_issues"] = [Obj(id="i1")]
    repo.responses["list_issues_by_type"] = [Obj(id="i2")]
    repo.responses["get_issue"] = Obj(
        id="i1",
        title="T",
        editorial_preface="",
        toc_json={},
        status="draft",
        total_pages=0,
        pdf_r2_key="",
        pdf_url="",
    )
    assert (await svc.list_issues())["issues"][0]["id"] == "i1"
    assert (await svc.list_issues(issue_type="weekly"))["issues"][0]["id"] == "i2"
    assert (await svc.get_issue("i1"))["scope"] == "admin"
    assert (await svc.create_issue("weekly", "Title", "slug"))["id"] == "id-2"
    assert (await svc.update_issue("i1", title="T2"))["id"] == "i1"
    assert (await svc.approve_issue("i1", "u1"))["id"] == "i1"
    assert (await svc.publish_issue("i1"))["id"] == "i1"
    await svc.delete_issue("i1")

    repo.responses["list_items"] = [Obj(id="it1")]
    repo.responses["get_item"] = Obj(
        id="it1",
        section="features",
        position=1,
        item_type="article",
        title="",
        excerpt="",
        include_full_content=True,
    )
    assert (await svc.list_items("i1"))[0]["id"] == "it1"
    assert (await svc.get_item("it1"))["id"] == "it1"
    assert (await svc.create_item("i1"))["id"] == "id-3"
    assert (await svc.update_item("it1", title="X"))["id"] == "it1"
    await svc.delete_item("it1")

    repo.responses["list_gen_runs"] = [Obj(id="gr1")]
    repo.responses["get_gen_run"] = Obj(id="gr1")
    assert (await svc.list_gen_runs("i1"))[0]["id"] == "gr1"
    assert (await svc.create_gen_run("i1", "job"))["id"] == "id-4"
    assert (await svc.update_gen_run("gr1", "done"))["id"] == "gr1"

    repo.responses["list_deliveries"] = [Obj(id="d1")]
    repo.responses["get_delivery"] = Obj(id="d1")
    assert (await svc.list_deliveries("i1"))["deliveries"][0]["id"] == "d1"
    assert (await svc.create_delivery("i1", "a@b.com"))["id"] == "id-5"
    assert (await svc.update_delivery_status("d1", "sent"))["id"] == "d1"


@pytest.mark.asyncio
async def test_publication_service_not_found(publication_service):
    svc, repo = publication_service
    repo.responses["get_subscription"] = None
    with pytest.raises(ValueError, match="Subscription not found"):
        await svc.get_subscription("x")
    repo.responses["get_issue"] = None
    with pytest.raises(ValueError, match="Publication issue not found"):
        await svc.get_issue("x")
    repo.responses["get_item"] = None
    with pytest.raises(ValueError, match="Item not found"):
        await svc.get_item("x")
    repo.responses["get_gen_run"] = None
    with pytest.raises(ValueError, match="Generation run not found"):
        await svc.update_gen_run("x", "failed")
    repo.responses["get_delivery"] = None
    with pytest.raises(ValueError, match="Delivery not found"):
        await svc.update_delivery_status("x", "failed")


@pytest.mark.asyncio
async def test_publication_repository_methods(monkeypatch):
    repo = PublicationRepository(db=object())
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

    await repo.list_subscriptions(20, 0)
    await repo.get_subscription("s1")
    await repo.get_subscription_by_email("a@b.com")
    await repo.create_subscription("s1", "a@b.com", "subscribed", "web")
    await repo.update_subscription_status("s1", "unsubscribed")
    await repo.delete_subscription("s1")
    await repo.list_issues(20, 0)
    await repo.list_issues_by_type("weekly", 20, 0)
    await repo.get_issue("i1")
    await repo.create_issue(
        "i1", "weekly", "T", "slug", "", "", "draft", "", {}, "", "u1"
    )
    await repo.update_issue("i1", "T", "", {}, "draft", 0, "", "")
    await repo.approve_issue("i1", "u1")
    await repo.publish_issue("i1")
    await repo.delete_issue("i1")
    await repo.list_items("i1")
    await repo.get_item("it1")
    await repo.create_item("it1", "i1", "a1", "features", 1, "article", "", "", True)
    await repo.update_item("it1", "features", 1, "article", "", "", True)
    await repo.delete_item("it1")
    await repo.list_gen_runs("i1")
    await repo.get_gen_run("gr1")
    await repo.create_gen_run("gr1", "i1", "job", "manual", "running")
    await repo.update_gen_run("gr1", "done", "", {})
    await repo.list_deliveries("i1", 20, 0)
    await repo.get_delivery("d1")
    await repo.create_delivery("d1", "i1", "a@b.com", "email", "queued")
    await repo.update_delivery_status("d1", "sent", "p", "mid", "")

    assert len(execute_calls) >= 15
