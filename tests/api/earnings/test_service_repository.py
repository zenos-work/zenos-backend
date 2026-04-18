import types

import pytest

from api.earnings import service as earnings_service_module
from api.earnings.repository import EarningsRepository
from api.earnings.service import EarningsService


class _Env:
    DB = object()


class Obj(types.SimpleNamespace):
    def to_dict(self, scope=None):
        data = dict(self.__dict__)
        if scope is not None:
            data["scope"] = scope
        return data


class RepoStub:
    def __init__(self):
        self.pending = False
        self.earnings = [Obj(id="e1", total_earnings_cents=3000, author_id="a1")]
        self.payouts = [Obj(id="p1")]
        self.tips = [Obj(id="t1")]
        self.reads = []
        self.upserts = []
        self.pending_payouts = []

    async def find_earnings_by_author(self, _author_id, _limit, _offset):
        return self.earnings

    async def count_earnings_by_author(self, _author_id):
        return len(self.earnings)

    async def earnings_summary(self, _author_id):
        return {"total_earnings_cents": 3000, "net_earnings_cents": 2700}

    async def find_payouts_by_author(self, _author_id, _limit, _offset):
        return self.payouts

    async def count_payouts_by_author(self, _author_id):
        return len(self.payouts)

    async def has_pending_payout(self, _author_id):
        return self.pending

    async def create_payout_request(self, *args):
        self.last_payout_request = args

    async def create_tip(self, *args):
        self.last_tip = args

    async def find_tips_received(self, _author_id, _limit, _offset):
        return self.tips

    async def count_tips_received(self, _author_id):
        return len(self.tips)

    async def premium_reads_for_period(self, _start, _end):
        return self.reads

    async def upsert_distribution_row(self, **kwargs):
        self.upserts.append(kwargs)

    async def create_pending_payout(self, **kwargs):
        self.pending_payouts.append(kwargs)

    async def earnings_by_period(self, _period_start):
        return self.earnings


@pytest.fixture
def earnings_service(monkeypatch):
    svc = EarningsService(_Env())
    repo = RepoStub()
    svc._repo = repo

    id_seq = iter(["id-1", "id-2", "id-3", "id-4", "id-5", "id-6"])
    monkeypatch.setattr(earnings_service_module, "new_id", lambda: next(id_seq))
    monkeypatch.setattr(
        earnings_service_module,
        "calculate_distribution",
        lambda **_kwargs: {
            "author_shares": {"a1": 2500, "a2": 1300},
            "eligible_payouts": {"a1": 2500},
        },
    )
    return svc, repo


@pytest.mark.asyncio
async def test_earnings_service_core_flows(earnings_service):
    svc, repo = earnings_service

    earnings = await svc.get_earnings("a1", page=2, limit=10)
    assert earnings["pagination"]["total"] == 1
    assert earnings["earnings"][0]["id"] == "e1"

    payouts = await svc.get_payouts("a1")
    assert payouts["payouts"][0]["id"] == "p1"

    pid = await svc.request_payout("a1", 2000, payout_method="stripe")
    assert pid == "id-1"

    tid = await svc.send_tip("u1", "a1", 1000, article_id="art1", is_anonymous=True)
    assert tid == "id-2"

    tips = await svc.get_tips_received("a1")
    assert tips["tips"][0]["scope"] == "author"

    repo.reads = [
        {"author_id": "a1", "article_id": "art1", "read_time_seconds": 12},
        {"author_id": "a1", "article_id": "art1", "read_time_seconds": 8},
        {"author_id": "a2", "article_id": "art2", "read_time_seconds": 4},
        {"author_id": "", "article_id": "art3", "read_time_seconds": 99},
    ]
    dist = await svc.calculate_monthly_distribution("2026-03-01", "2026-03-31", 100)
    assert dist["persisted_rows"] == 2
    assert dist["pending_payouts_created"] == 1
    assert len(repo.upserts) == 2
    assert len(repo.pending_payouts) == 1

    report = await svc.distribution_report("2026-03-01")
    assert report["authors_count"] == 1

    mine = await svc.my_breakdown("a1", "2026-03-01")
    assert mine["total_earnings_cents"] == 3000


@pytest.mark.asyncio
async def test_earnings_service_validations(earnings_service):
    svc, repo = earnings_service

    with pytest.raises(ValueError, match="Amount must be positive"):
        await svc.request_payout("a1", 0)

    with pytest.raises(ValueError, match="Invalid payout_method"):
        await svc.request_payout("a1", 1000, payout_method="crypto")

    repo.pending = True
    with pytest.raises(ValueError, match="pending payout already exists"):
        await svc.request_payout("a1", 1000)

    with pytest.raises(ValueError, match="Tip amount must be positive"):
        await svc.send_tip("u1", "a1", 0)

    with pytest.raises(ValueError, match="Cannot tip yourself"):
        await svc.send_tip("a1", "a1", 100)


@pytest.mark.asyncio
async def test_earnings_repository_methods(monkeypatch):
    repo = EarningsRepository(db=object())

    execute_calls = []
    find_all_calls = []
    find_one_calls = []

    async def _execute(sql, *params):
        execute_calls.append((sql, params))

    async def _find_all(sql, *params):
        find_all_calls.append((sql, params))
        return [{"id": "x", "author_id": "a1"}, {"id": "y", "author_id": "a2"}]

    async def _find_one(sql, *params):
        find_one_calls.append((sql, params))
        if "pending" in str(sql).lower():
            return {"id": "p1"}
        return {
            "c": 2,
            "total_earnings": 1000,
            "net_earnings": 900,
            "total_fees": 100,
            "total_reads": 20,
        }

    monkeypatch.setattr(repo, "execute", _execute)
    monkeypatch.setattr(repo, "find_all", _find_all)
    monkeypatch.setattr(repo, "find_one", _find_one)
    monkeypatch.setattr(repo, "map_many", lambda rows, _model: rows)

    assert await repo.find_earnings_by_author("a1", 20, 0) == [
        {"id": "x", "author_id": "a1"},
        {"id": "y", "author_id": "a2"},
    ]
    assert await repo.count_earnings_by_author("a1") == 2
    summary = await repo.earnings_summary("a1")
    assert summary["net_earnings_cents"] == 900

    assert await repo.find_payouts_by_author("a1", 20, 0) == [
        {"id": "x", "author_id": "a1"},
        {"id": "y", "author_id": "a2"},
    ]
    assert await repo.count_payouts_by_author("a1") == 2
    assert await repo.has_pending_payout("a1") is True

    await repo.create_payout_request(
        "p1", "a1", 1000, "USD", "stripe", "2026-03-01", "2026-03-31"
    )
    await repo.create_tip("t1", "u1", "a1", 500, 50, 450, "art1", "USD", "nice", 1)

    assert await repo.find_tips_received("a1", 20, 0) == [
        {"id": "x", "author_id": "a1"},
        {"id": "y", "author_id": "a2"},
    ]
    assert await repo.count_tips_received("a1") == 2

    reads = await repo.premium_reads_for_period("2026-03-01", "2026-03-31")
    assert reads[0]["id"] == "x"

    period_rows = await repo.earnings_by_period("2026-03-01")
    assert period_rows[1]["author_id"] == "a2"

    await repo.upsert_distribution_row(
        "e1", "a1", "2026-03-01", "2026-03-31", 1000, 10, 300, 2
    )
    await repo.create_pending_payout("p2", "a1", 1000, "2026-03-01", "2026-03-31")

    assert len(execute_calls) == 4
    assert len(find_all_calls) == 5
    assert len(find_one_calls) == 5
