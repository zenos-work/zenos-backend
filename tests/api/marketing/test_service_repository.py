import types

import pytest

from api.marketing import service as marketing_service_module
from api.marketing.repository import MarketingRepository
from api.marketing.service import MarketingService


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
def mkt_service(monkeypatch):
    svc = MarketingService(_Env())
    repo = RepoDyn()
    svc._repo = repo
    seq = iter([f"id-{i}" for i in range(1, 60)])
    monkeypatch.setattr(marketing_service_module, "new_id", lambda: next(seq))
    return svc, repo


@pytest.mark.asyncio
async def test_marketing_service_happy_paths(mkt_service):
    svc, repo = mkt_service

    repo.responses["list_channels"] = [Obj(id="ch1")]
    repo.responses["get_channel"] = Obj(
        id="ch1", name="Channel", channel_type="x", config={}, is_active=True
    )
    assert (await svc.list_channels("o1"))[0]["id"] == "ch1"
    assert (await svc.get_channel("ch1"))["scope"] == "admin"
    assert (await svc.create_channel("o1", "N", "email"))["id"] == "id-1"
    assert (await svc.update_channel("ch1", name="N2"))["id"] == "ch1"
    await svc.delete_channel("ch1")

    repo.responses["list_scheduled"] = [Obj(id="s1")]
    repo.responses["get_scheduled"] = Obj(id="s1")
    assert (await svc.list_scheduled("u1"))[0]["id"] == "s1"
    assert (await svc.get_scheduled("s1"))["id"] == "s1"
    assert (await svc.create_scheduled("a1", "u1", "2026-01-01"))["id"] == "id-2"
    assert (await svc.update_scheduled_status("s1", "done"))["id"] == "s1"
    await svc.delete_scheduled("s1")

    repo.responses["list_dist_jobs"] = [Obj(id="j1")]
    repo.responses["get_dist_job"] = Obj(id="j1")
    assert (await svc.list_dist_jobs("o1"))["jobs"][0]["id"] == "j1"
    assert (await svc.get_dist_job("j1"))["id"] == "j1"
    assert (await svc.create_dist_job("o1", "a1", "ch1", "2026-01-01"))["id"] == "id-3"
    assert (await svc.update_dist_job_status("j1", "done"))["id"] == "j1"

    repo.responses["list_syndications"] = [Obj(id="sy1")]
    assert (await svc.list_syndications("a1"))[0]["id"] == "sy1"
    assert (await svc.create_syndication("a1", "medium", "https://x"))["id"] == "id-4"
    await svc.delete_syndication("sy1")

    repo.responses["list_rss_feeds"] = [Obj(id="r1")]
    repo.responses["get_rss_feed"] = Obj(
        id="r1",
        name="F",
        description="",
        filter_tags=[],
        filter_authors=[],
        max_items=50,
        include_premium=False,
        is_active=True,
    )
    assert (await svc.list_rss_feeds("o1"))[0]["id"] == "r1"
    assert (await svc.get_rss_feed("r1"))["id"] == "r1"
    assert (await svc.create_rss_feed("o1", "F", "f"))["id"] == "id-5"
    assert (await svc.update_rss_feed("r1", name="F2"))["id"] == "r1"
    await svc.delete_rss_feed("r1")

    repo.responses["list_repurposing"] = [Obj(id="rp1")]
    repo.responses["get_repurposing"] = Obj(id="rp1")
    assert (await svc.list_repurposing("o1"))["jobs"][0]["id"] == "rp1"
    assert (await svc.get_repurposing("rp1"))["id"] == "rp1"
    assert (await svc.create_repurposing("o1", "a1", "thread"))["id"] == "id-6"
    assert (await svc.update_repurposing_status("rp1", "done"))["id"] == "rp1"

    repo.responses["list_campaigns"] = [Obj(id="c1")]
    repo.responses["get_campaign"] = Obj(
        id="c1",
        name="C",
        description="",
        status="active",
        start_date="",
        end_date="",
        budget_cents=0,
    )
    assert (await svc.list_campaigns("o1"))["campaigns"][0]["id"] == "c1"
    assert (await svc.get_campaign("c1"))["id"] == "c1"
    assert (await svc.create_campaign("o1", "C"))["id"] == "id-7"
    assert (await svc.update_campaign("c1", name="C2"))["id"] == "c1"
    await svc.delete_campaign("c1")

    repo.responses["list_campaign_articles"] = ["a1"]
    assert await svc.list_campaign_articles("c1") == ["a1"]
    await svc.add_campaign_article("c1", "a2")
    await svc.remove_campaign_article("c1", "a2")


@pytest.mark.asyncio
async def test_marketing_service_not_found(mkt_service):
    svc, repo = mkt_service

    repo.responses["get_channel"] = None
    with pytest.raises(ValueError, match="Channel not found"):
        await svc.get_channel("missing")

    repo.responses["get_scheduled"] = None
    with pytest.raises(ValueError, match="Scheduled publication not found"):
        await svc.get_scheduled("missing")

    repo.responses["get_dist_job"] = None
    with pytest.raises(ValueError, match="Distribution job not found"):
        await svc.get_dist_job("missing")

    repo.responses["get_rss_feed"] = None
    with pytest.raises(ValueError, match="RSS feed not found"):
        await svc.get_rss_feed("missing")

    repo.responses["get_repurposing"] = None
    with pytest.raises(ValueError, match="Repurposing job not found"):
        await svc.get_repurposing("missing")

    repo.responses["get_campaign"] = None
    with pytest.raises(ValueError, match="Campaign not found"):
        await svc.get_campaign("missing")


@pytest.mark.asyncio
async def test_marketing_repository_methods(monkeypatch):
    repo = MarketingRepository(db=object())
    execute_calls = []
    find_all_calls = []
    find_one_calls = []

    async def _execute(sql, *params):
        execute_calls.append((sql, params))

    async def _find_all(sql, *params):
        find_all_calls.append((sql, params))
        if "campaign_articles" in str(sql).lower():
            return [{"article_id": "a1"}, {"article_id": "a2"}]
        return [{"id": "x"}, {"id": "y"}]

    async def _find_one(sql, *params):
        find_one_calls.append((sql, params))
        return {"id": "x"}

    monkeypatch.setattr(repo, "execute", _execute)
    monkeypatch.setattr(repo, "find_all", _find_all)
    monkeypatch.setattr(repo, "find_one", _find_one)
    monkeypatch.setattr(repo, "map_many", lambda rows, _model: rows)
    monkeypatch.setattr(repo, "map_one", lambda row, _model: row)

    await repo.list_channels("o1")
    await repo.get_channel("ch1")
    await repo.create_channel("ch1", "o1", "N", "email", {}, "", True, "u1")
    await repo.update_channel("ch1", "N", "email", {}, False)
    await repo.delete_channel("ch1")
    await repo.list_scheduled("u1")
    await repo.get_scheduled("s1")
    await repo.get_scheduled_by_article("a1")
    await repo.create_scheduled("s1", "a1", "u1", "2026-01-01", "UTC")
    await repo.update_scheduled_status("s1", "done")
    await repo.delete_scheduled("s1")
    await repo.list_dist_jobs("o1", 20, 0)
    await repo.get_dist_job("j1")
    await repo.create_dist_job("j1", "o1", "a1", "ch1", "2026-01-01", "")
    await repo.update_dist_job_status("j1", "done")
    await repo.list_syndications("a1")
    await repo.create_syndication("sy1", "a1", "medium", "https://x", True)
    await repo.delete_syndication("sy1")
    await repo.list_rss_feeds("o1")
    await repo.get_rss_feed("r1")
    await repo.get_rss_feed_by_slug("o1", "slug")
    await repo.create_rss_feed("r1", "o1", "N", "slug", "", [], [], 50, False, True)
    await repo.update_rss_feed("r1", "N", "", [], [], 50, False, True)
    await repo.delete_rss_feed("r1")
    await repo.list_repurposing("o1", 20, 0)
    await repo.get_repurposing("rp1")
    await repo.create_repurposing("rp1", "o1", "a1", "thread", {}, "u1")
    await repo.update_repurposing_status("rp1", "done", "")
    await repo.list_campaigns("o1", 20, 0)
    await repo.get_campaign("c1")
    await repo.create_campaign("c1", "o1", "N", "", "content", "", "", 0, "", "u1")
    await repo.update_campaign("c1", "N", "", "active", "", "", 0)
    await repo.delete_campaign("c1")
    assert await repo.list_campaign_articles("c1") == ["a1", "a2"]
    await repo.add_campaign_article("c1", "a1")
    await repo.remove_campaign_article("c1", "a1")

    assert len(execute_calls) == 20
    assert len(find_all_calls) == 8
    assert len(find_one_calls) == 8
