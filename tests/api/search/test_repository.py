import importlib

import pytest


SearchRepository = importlib.import_module("api.search.repository").SearchRepository
Q = importlib.import_module("api.search.queries")


@pytest.mark.asyncio
async def test_extract_count_handles_missing_and_value():
    assert SearchRepository._extract_count(None) == 0
    assert SearchRepository._extract_count({"c": "7"}) == 7


@pytest.mark.asyncio
async def test_find_and_count_articles_with_filters(monkeypatch):
    repo = SearchRepository(None)

    captured = {}

    async def _find_all(sql, *params):
        captured["find_all"] = (sql, params)
        return [{"id": "a1"}]

    async def _find_one(sql, *params):
        captured["find_one"] = (sql, params)
        return {"c": 4}

    repo.find_all = _find_all
    repo.find_one = _find_one
    repo.map_many = lambda rows, model_cls: ["mapped-article"]

    items = await repo.find_articles(
        "fintech*",
        10,
        20,
        status="PUBLISHED",
        content_type="research",
        outcome_tag="roi",
        verified_only=True,
    )
    total = await repo.count_articles(
        "fintech*",
        status="PUBLISHED",
        content_type="research",
        outcome_tag="roi",
        verified_only=True,
    )

    assert items == ["mapped-article"]
    assert total == 4

    sql_all, params_all = captured["find_all"]
    assert sql_all == Q.SELECT_ARTICLES_FTS
    assert params_all[4] == "research"
    assert params_all[5] == 1
    assert params_all[6] == "roi"

    sql_one, params_one = captured["find_one"]
    assert sql_one == Q.COUNT_ARTICLES_FTS
    assert params_one[5] == 1


@pytest.mark.asyncio
async def test_find_and_count_tags_and_authors(monkeypatch):
    repo = SearchRepository(None)

    calls = []

    async def _find_all(sql, *params):
        calls.append(("all", sql, params))
        return [{"id": "x"}]

    async def _find_one(sql, *params):
        calls.append(("one", sql, params))
        return {"c": 2}

    repo.find_all = _find_all
    repo.find_one = _find_one
    repo.map_many = lambda rows, model_cls: ["mapped"]

    tags = await repo.find_tags("%fin%", 5, 0)
    tag_total = await repo.count_tags("%fin%")
    authors = await repo.find_authors("%author%", 5, 5)
    author_total = await repo.count_authors("%author%")

    assert tags == ["mapped"]
    assert authors == ["mapped"]
    assert tag_total == 2
    assert author_total == 2

    assert ("all", Q.SELECT_TAGS_SEARCH, ("%fin%", "%fin%", 5, 0)) in calls
    assert ("one", Q.COUNT_TAGS_SEARCH, ("%fin%", "%fin%")) in calls
    assert ("all", Q.SELECT_AUTHORS_SEARCH, ("%author%", 5, 5)) in calls
    assert ("one", Q.COUNT_AUTHORS_SEARCH, ("%author%",)) in calls
