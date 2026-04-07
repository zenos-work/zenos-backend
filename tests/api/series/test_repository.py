import importlib

import pytest


SeriesRepository = importlib.import_module("api.series.repository").SeriesRepository
Q = importlib.import_module("api.series.queries")


@pytest.mark.asyncio
async def test_schema_detection_and_missing_table_handling():
    repo = SeriesRepository(None)

    calls = {"find_one": []}

    async def _find_one(sql, *params):
        calls["find_one"].append((sql, params))
        if "sqlite_master" in sql:
            return {"table_count": 2}
        if sql == Q.SELECT_ARTICLE_SERIES:
            return {"series_id": "s1", "part_number": 1}
        return {"id": "s1"}

    repo.find_one = _find_one
    repo.map_one = lambda row, model_cls: {"mapped": row}

    assert await repo._has_series_schema() is True
    # Cached second call should not query sqlite_master again.
    assert await repo._has_series_schema() is True

    info = await repo.find_article_series("a1")
    assert info["mapped"]["series_id"] == "s1"

    async def _find_one_missing(sql, *params):
        if "sqlite_master" in sql:
            return {"table_count": 2}
        raise RuntimeError("no such table: article_series")

    repo2 = SeriesRepository(None)
    repo2.find_one = _find_one_missing
    repo2.map_one = lambda row, model_cls: row

    assert await repo2.find_article_series("a2") is None
    assert repo2._series_schema_ready is False


@pytest.mark.asyncio
async def test_read_queries_and_exists_checks():
    repo = SeriesRepository(None)

    async def _find_all(sql, *params):
        if sql == Q.SELECT_SERIES_BY_AUTHOR:
            return [{"id": "s1"}]
        return [{"id": "a1"}]

    async def _find_one(sql, *params):
        if sql == Q.SELECT_SERIES_BY_AUTHOR_COUNT:
            return {"total": 7}
        if sql == Q.SELECT_SERIES_EXISTS:
            return {"ok": 1}
        if sql == Q.SELECT_ARTICLE_SERIES_EXISTS:
            return None
        return {"id": "s1"}

    repo.find_all = _find_all
    repo.find_one = _find_one
    repo.map_one = lambda row, model_cls: row
    repo.map_many = lambda rows, model_cls: rows

    by_id = await repo.find_by_id("s1")
    by_author = await repo.find_by_author("u1", page=2, limit=3)
    series_articles = await repo.find_series_articles("s1")

    assert by_id["id"] == "s1"
    assert by_author.total == 7
    assert by_author.page == 2
    assert len(series_articles) == 1
    assert await repo.exists("s1", "u1") is True
    assert await repo.article_series_exists("a1", "s1") is False


@pytest.mark.asyncio
async def test_write_queries_parameter_shapes():
    repo = SeriesRepository(None)
    executed = []

    async def _execute(sql, *params):
        executed.append((sql, params))

    repo.execute = _execute

    await repo.create("s1", "u1", "Series", None, None, "c", "u")
    await repo.update("s1", "u1", "New", None, None, "u2")
    await repo.assign_article("as1", "a1", "s1", 1, "c", "u")
    await repo.update_article_part("a1", "s1", 2, "u3")
    await repo.remove_article("a1", "s1")
    await repo.delete("s1", "u1")

    assert executed[0][0] == Q.INSERT_SERIES
    assert executed[1][0] == Q.UPDATE_SERIES
    assert executed[2][0] == Q.INSERT_ARTICLE_SERIES
    assert executed[3][0] == Q.UPDATE_ARTICLE_SERIES_PART
    assert executed[4][0] == Q.DELETE_ARTICLE_SERIES
    assert executed[5][0] == Q.DELETE_SERIES


def test_missing_series_table_detector():
    assert SeriesRepository._is_missing_series_table_error(
        RuntimeError("no such table: series")
    )
    assert SeriesRepository._is_missing_series_table_error(
        RuntimeError("No Such Table: article_series")
    )
    assert not SeriesRepository._is_missing_series_table_error(
        RuntimeError("permission denied")
    )
