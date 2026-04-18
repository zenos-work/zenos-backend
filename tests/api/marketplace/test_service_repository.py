import types

import pytest

from api.marketplace import service as marketplace_service_module
from api.marketplace.repository import MarketplaceRepository
from api.marketplace.service import MarketplaceService


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
def marketplace_service(monkeypatch):
    svc = MarketplaceService(_Env())
    repo = RepoDyn()
    svc._repo = repo
    seq = iter([f"id-{i}" for i in range(1, 60)])
    monkeypatch.setattr(marketplace_service_module, "new_id", lambda: next(seq))
    return svc, repo


@pytest.mark.asyncio
async def test_marketplace_service_happy_paths(marketplace_service):
    svc, repo = marketplace_service

    repo.responses["list_items"] = [Obj(id="i1")]
    repo.responses["list_items_by_category"] = [Obj(id="i2")]
    repo.responses["list_items_by_seller"] = [Obj(id="i3")]
    repo.responses["get_item"] = Obj(
        id="i1",
        name="N",
        short_desc="S",
        long_desc="",
        item_type="workflow",
        category="cat",
        price_cents=0,
        currency="USD",
        pricing_model="one_time",
        preview_images=[],
        asset_url="",
        workflow_id="",
        status="draft",
    )
    assert (await svc.list_items())["items"][0]["id"] == "i1"
    assert (await svc.list_items(category="cat"))["items"][0]["id"] == "i2"
    assert (await svc.list_items(seller_id="u1"))["items"][0]["id"] == "i3"
    assert (await svc.get_item("i1"))["id"] == "i1"
    assert (await svc.create_item("u1", "N", "slug", "S", "cat"))["id"] == "id-1"
    assert (await svc.update_item("i1", name="N2"))["id"] == "i1"
    await svc.delete_item("i1")
    assert (await svc.publish_item("i1"))["status"] == "published"

    repo.responses["list_purchases_by_buyer"] = [Obj(id="p1")]
    repo.responses["list_purchases_by_item"] = [Obj(id="p2")]
    repo.responses["get_purchase_by_buyer_item"] = None
    assert (await svc.list_purchases("u1"))["purchases"][0]["id"] == "p1"
    assert (await svc.list_item_purchases("i1"))["purchases"][0]["id"] == "p2"
    assert (await svc.purchase_item("i1", "u1"))["id"] == "id-2"

    repo.responses["list_reviews"] = [Obj(id="r1")]
    repo.responses["get_review_by_reviewer"] = None
    repo.responses["get_review"] = Obj(id="r1")
    assert (await svc.list_reviews("i1"))["reviews"][0]["id"] == "r1"
    assert (await svc.create_review("i1", "u2", 5))["id"] == "id-3"
    await svc.delete_review("r1")


@pytest.mark.asyncio
async def test_marketplace_service_not_found(marketplace_service):
    svc, repo = marketplace_service
    repo.responses["get_item"] = None
    with pytest.raises(ValueError, match="Item not found"):
        await svc.get_item("x")
    repo.responses["get_purchase_by_buyer_item"] = Obj(id="x")
    with pytest.raises(ValueError, match="Already purchased"):
        await svc.purchase_item("i1", "u1")
    repo.responses["get_review_by_reviewer"] = Obj(id="x")
    with pytest.raises(ValueError, match="Already reviewed"):
        await svc.create_review("i1", "u1", 5)
    repo.responses["get_review"] = None
    with pytest.raises(ValueError, match="Review not found"):
        await svc.delete_review("x")


@pytest.mark.asyncio
async def test_marketplace_repository_methods(monkeypatch):
    repo = MarketplaceRepository(db=object())
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

    await repo.list_items(20, 0)
    await repo.list_items_by_seller("u1", 20, 0)
    await repo.list_items_by_category("cat", 20, 0)
    await repo.get_item("i1")
    await repo.create_item(
        "i1",
        "u1",
        "o1",
        "N",
        "slug",
        "S",
        "",
        "workflow",
        "cat",
        0,
        "USD",
        "one_time",
        [],
        "",
        "",
        "draft",
    )
    await repo.update_item(
        "i1", "N", "S", "", "workflow", "cat", 0, "USD", "one_time", [], "", "", "draft"
    )
    await repo.delete_item("i1")
    await repo.publish_item("i1")
    await repo.increment_purchase_count("i1")
    await repo.update_rating("i1", 5)
    await repo.list_purchases_by_buyer("u1", 20, 0)
    await repo.list_purchases_by_item("i1", 20, 0)
    await repo.get_purchase("p1")
    await repo.get_purchase_by_buyer_item("i1", "u1")
    await repo.create_purchase("p1", "i1", "u1", "o1", "pay", 100, "USD", "completed")
    await repo.list_reviews("i1", 20, 0)
    await repo.get_review("r1")
    await repo.get_review_by_reviewer("i1", "u1")
    await repo.create_review("r1", "i1", "u1", 5, "good")
    await repo.delete_review("r1")

    assert len(execute_calls) >= 9
