import pytest

from api.analytics.repository import AnalyticsRepository
from api.analytics.service import AnalyticsService


class _Env:
    DB = object()


class _Log:
    def __init__(self):
        self.events = []

    async def event(self, name, data=None):
        self.events.append((name, data))


class _Ctx:
    def __init__(self):
        self.log = _Log()


@pytest.mark.asyncio
async def test_record_article_event_calls_repo_with_defaults(monkeypatch):
    service = AnalyticsService(_Env())

    calls = []

    async def _record(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(service._repo, "record_article_event", _record)

    await service.record_article_event(article_id="a1", event_type="VIEW")

    assert len(calls) == 1
    payload = calls[0]
    assert payload["article_id"] == "a1"
    assert payload["event_type"] == "VIEW"
    assert payload["event_source"] == "api"
    assert payload["event_value"] == 1
    assert payload["event_id"]


@pytest.mark.asyncio
async def test_aggregate_previous_hour_runs_repo_and_logs(monkeypatch):
    ctx = _Ctx()
    service = AnalyticsService(_Env(), ctx)

    async def _count(_start, _end):
        return 5

    aggregate_calls = []

    async def _aggregate(bucket_hour, window_start, window_end):
        aggregate_calls.append((bucket_hour, window_start, window_end))

    monkeypatch.setattr(service._repo, "count_events_in_window", _count)
    monkeypatch.setattr(service._repo, "aggregate_hour", _aggregate)

    result = await service.aggregate_previous_hour()

    assert result["events_processed"] == 5
    assert aggregate_calls
    assert result["bucket_hour"] == aggregate_calls[0][0]
    assert (
        ctx.log.events and ctx.log.events[0][0] == "sr011.hourly_aggregation.completed"
    )


@pytest.mark.asyncio
async def test_repository_record_and_aggregate_sql_paths(monkeypatch):
    repo = AnalyticsRepository(db=object())

    execute_calls = []

    async def _execute(sql, *params):
        execute_calls.append((sql, params))

    monkeypatch.setattr(repo, "execute", _execute)

    await repo.record_article_event(
        event_id="e1",
        article_id="a1",
        event_type="LIKE",
        actor_user_id="u1",
        event_value=1,
        event_source="api",
        metadata_json='{"x":1}',
    )
    await repo.aggregate_hour(
        "2026-03-24 09:00:00", "2026-03-24 09:00:00", "2026-03-24 10:00:00"
    )

    assert len(execute_calls) == 2


@pytest.mark.asyncio
async def test_repository_count_events_in_window(monkeypatch):
    repo = AnalyticsRepository(db=object())

    async def _find_one(_sql, *_params):
        return {"count": 7}

    monkeypatch.setattr(repo, "find_one", _find_one)

    count = await repo.count_events_in_window(
        "2026-03-24 09:00:00", "2026-03-24 10:00:00"
    )
    assert count == 7
