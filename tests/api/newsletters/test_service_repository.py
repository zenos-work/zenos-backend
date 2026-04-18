import types

import pytest

from api.newsletters import service as newsletters_service_module
from api.newsletters.repository import NewsletterRepository
from api.newsletters.service import NewsletterService


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
def newsletter_service(monkeypatch):
    svc = NewsletterService(_Env())
    repo = RepoDyn()
    svc._repo = repo
    seq = iter([f"id-{i}" for i in range(1, 80)])
    monkeypatch.setattr(newsletters_service_module, "new_id", lambda: next(seq))
    return svc, repo


@pytest.mark.asyncio
async def test_newsletter_service_happy_paths(newsletter_service):
    svc, repo = newsletter_service
    repo.responses["list_newsletters"] = [Obj(id="n1")]
    repo.responses["list_newsletters_by_owner"] = [Obj(id="n2")]
    repo.responses["get_newsletter"] = Obj(
        id="n1",
        name="N",
        description="",
        logo_url="",
        cover_url="",
        from_name="F",
        from_email="f@example.com",
        reply_to_email="",
        is_premium_only=False,
        membership_tier="",
        status="active",
    )
    assert (await svc.list_newsletters("o1"))[0]["id"] == "n1"
    assert (await svc.list_newsletters_by_owner("u1"))[0]["id"] == "n2"
    assert (await svc.get_newsletter("n1"))["scope"] == "admin"
    assert (await svc.create_newsletter("o1", "u1", "N", "n"))["id"] == "id-1"
    assert (await svc.update_newsletter("n1", name="N2"))["id"] == "n1"
    await svc.delete_newsletter("n1")

    repo.responses["list_subscribers"] = [Obj(id="s1")]
    repo.responses["get_subscriber"] = Obj(
        id="s1", status="subscribed", newsletter_id="n1"
    )
    assert (await svc.list_subscribers("n1"))["subscribers"][0]["id"] == "s1"
    assert (await svc.get_subscriber("s1"))["scope"] == "admin"
    assert (await svc.create_subscriber("n1", "a@b.com"))["id"] == "id-2"
    assert (await svc.update_subscriber_status("s1", "unsubscribed"))["id"] == "s1"
    await svc.delete_subscriber("s1")

    repo.responses["list_issues"] = [Obj(id="i1")]
    repo.responses["get_issue"] = Obj(
        id="i1",
        subject="S",
        preview_text="",
        body_html="",
        body_text="",
        issue_type="digest",
        article_ids=[],
        status="draft",
        scheduled_at="",
    )
    assert (await svc.list_issues("n1"))["issues"][0]["id"] == "i1"
    assert (await svc.get_issue("i1"))["scope"] == "admin"
    assert (await svc.create_issue("n1", "S"))["id"] == "id-3"
    assert (await svc.update_issue("i1", subject="S2"))["id"] == "i1"
    assert (await svc.update_issue_status("i1", "sent"))["id"] == "i1"
    await svc.delete_issue("i1")

    repo.responses["list_issue_articles"] = [Obj(id="ia1")]
    assert (await svc.list_issue_articles("i1"))[0]["id"] == "ia1"
    await svc.add_issue_article("i1", "a1")
    await svc.remove_issue_article("i1", "a1")

    repo.responses["list_send_events"] = [Obj(id="e1")]
    assert (await svc.list_send_events("i1"))["events"][0]["id"] == "e1"
    assert (await svc.create_send_event("i1", "s1", "open"))["id"] == "id-4"

    repo.responses["list_segments"] = [Obj(id="seg1")]
    repo.responses["get_segment"] = Obj(id="seg1", name="Seg", filter_rules={})
    assert (await svc.list_segments("n1"))[0]["id"] == "seg1"
    assert (await svc.get_segment("seg1"))["id"] == "seg1"
    assert (await svc.create_segment("n1", "Seg"))["id"] == "id-5"
    assert (await svc.update_segment("seg1", name="Seg2"))["id"] == "seg1"
    await svc.delete_segment("seg1")


@pytest.mark.asyncio
async def test_newsletter_service_not_found(newsletter_service):
    svc, repo = newsletter_service
    repo.responses["get_newsletter"] = None
    with pytest.raises(ValueError, match="Newsletter not found"):
        await svc.get_newsletter("x")

    repo.responses["get_subscriber"] = None
    with pytest.raises(ValueError, match="Subscriber not found"):
        await svc.get_subscriber("x")

    repo.responses["get_issue"] = None
    with pytest.raises(ValueError, match="Issue not found"):
        await svc.get_issue("x")

    repo.responses["get_segment"] = None
    with pytest.raises(ValueError, match="Segment not found"):
        await svc.get_segment("x")


@pytest.mark.asyncio
async def test_newsletter_repository_methods(monkeypatch):
    repo = NewsletterRepository(db=object())
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

    await repo.list_newsletters("o1")
    await repo.list_newsletters_by_owner("u1")
    await repo.get_newsletter("n1")
    await repo.create_newsletter(
        "n1", "o1", "u1", "N", "n", "", "", "", "", "", "", False, "", "active"
    )
    await repo.update_newsletter("n1", "N", "", "", "", "", "", "", False, "", "active")
    await repo.delete_newsletter("n1")
    await repo.increment_subscriber_count("n1")
    await repo.decrement_subscriber_count("n1")
    await repo.list_subscribers("n1", 20, 0)
    await repo.get_subscriber("s1")
    await repo.get_subscriber_by_email("n1", "a@b.com")
    await repo.create_subscriber("s1", "n1", "a@b.com", "A", "B", "web", "subscribed")
    await repo.update_subscriber_status("s1", "unsubscribed")
    await repo.delete_subscriber("s1")
    await repo.list_issues("n1", 20, 0)
    await repo.get_issue("i1")
    await repo.create_issue(
        "i1", "n1", "S", "", "", "", "digest", [], "draft", "", "u1"
    )
    await repo.update_issue("i1", "S", "", "", "", "digest", [], "draft", "")
    await repo.update_issue_status("i1", "sent")
    await repo.delete_issue("i1")
    await repo.list_issue_articles("i1")
    await repo.add_issue_article("i1", "a1", 0, "")
    await repo.remove_issue_article("i1", "a1")
    await repo.list_send_events("i1", 20, 0)
    await repo.create_send_event("e1", "i1", "s1", "open", "", {})
    await repo.list_segments("n1")
    await repo.get_segment("seg1")
    await repo.create_segment("seg1", "n1", "Seg", {})
    await repo.update_segment("seg1", "Seg", {})
    await repo.delete_segment("seg1")

    assert len(execute_calls) >= 18
