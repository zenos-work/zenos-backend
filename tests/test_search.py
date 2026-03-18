import pytest
import sys
import types
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Stub out the `workers` and `js` C-extension modules that are only available
# inside the Cloudflare Workers runtime.
if "workers" not in sys.modules:
    workers_stub = types.ModuleType("workers")

    class _WorkerEntrypoint:
        pass

    workers_stub.WorkerEntrypoint = _WorkerEntrypoint
    sys.modules["workers"] = workers_stub

if "js" not in sys.modules:
    js_stub = types.ModuleType("js")

    class _Headers:
        @staticmethod
        def new(*args, **kwargs):
            return None

    class _Response:
        def __init__(self, body=None, status=200, headers=None):
            self.body = body
            self.status = status

        @staticmethod
        def new(body=None, status=200, headers=None):
            return _Response(body, status, headers)

    js_stub.Headers = _Headers
    js_stub.Response = _Response
    sys.modules["js"] = js_stub


search_service_mod = importlib.import_module("api.search.service")
SearchService = search_service_mod.SearchService
_fts_query = search_service_mod._fts_query
_like_pattern = search_service_mod._like_pattern

Tag = importlib.import_module("models.tag.model").Tag
User = importlib.import_module("models.user.model").User


# ── Helpers ───────────────────────────────────────────────────────────────────


def make_tag(name="python", slug="python") -> Tag:
    return Tag(id="t1", name=name, slug=slug, article_count=3)


def make_user(name="Alice") -> User:
    return User(
        id="u1",
        email="alice@example.com",
        name=name,
        role="AUTHOR",
        is_active=1,
        created_at="2024-01-01",
        updated_at="2024-01-01",
    )


class DummyCtx:
    class _Log:
        async def analytics(self, name, data=None):
            return None

    log = _Log()


class DummyEnv:
    DB = None


class DummyRepo:
    def __init__(self):
        self.articles = []
        self.articles_count = 0
        self.tags = []
        self.tags_count = 0
        self.authors = []
        self.authors_count = 0

    async def find_articles(self, fts_query, limit, offset):
        return self.articles

    async def count_articles(self, fts_query):
        return self.articles_count

    async def find_tags(self, like_pattern, limit, offset):
        return self.tags

    async def count_tags(self, like_pattern):
        return self.tags_count

    async def find_authors(self, like_pattern, limit, offset):
        return self.authors

    async def count_authors(self, like_pattern):
        return self.authors_count


# ── _fts_query sanitiser tests ────────────────────────────────────────────────


def test_fts_query_basic_words():
    result = _fts_query("machine learning")
    assert result == "machine* learning*"


def test_fts_query_prefix_star_per_token():
    result = _fts_query("fintech")
    assert result == "fintech*"


def test_fts_query_strips_special_chars():
    result = _fts_query('hello "world"')
    assert result == "hello* world*"


def test_fts_query_returns_none_for_all_special_chars():
    assert _fts_query("!!!") is None
    assert _fts_query("---") is None


def test_fts_query_returns_none_for_empty_string():
    assert _fts_query("") is None


def test_fts_query_truncates_at_200_chars():
    long_q = "a " * 200  # 400 chars
    result = _fts_query(long_q)
    # Should still produce valid output from the first 200 chars
    assert result is not None
    assert "*" in result


# ── _like_pattern tests ───────────────────────────────────────────────────────


def test_like_pattern_wraps_in_percent():
    assert _like_pattern("python") == "%python%"


def test_like_pattern_escapes_wildcards():
    assert _like_pattern("100%") == "%100\\%%"
    assert _like_pattern("some_field") == "%some\\_field%"


def test_like_pattern_strips_surrounding_whitespace():
    result = _like_pattern("  finance  ")
    assert result == "%finance%"


# ── SearchService.search_articles ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_articles_returns_paginated_response():
    svc = SearchService(DummyEnv(), DummyCtx())
    repo = DummyRepo()
    repo.articles = ["a1", "a2"]
    repo.articles_count = 42
    svc._repo = repo

    result = await svc.search_articles("machine learning", page=1)

    assert result.items == ["a1", "a2"]
    assert result.total == 42
    assert result.page == 1


@pytest.mark.asyncio
async def test_search_articles_has_more_when_full_page():
    svc = SearchService(DummyEnv(), DummyCtx())
    repo = DummyRepo()
    # Return exactly PAGE_SIZE items → has_more should be True
    repo.articles = ["a"] * 20
    repo.articles_count = 100
    svc._repo = repo

    result = await svc.search_articles("python", page=1)

    assert result.has_more is True


@pytest.mark.asyncio
async def test_search_articles_empty_fts_returns_empty_response():
    """Queries containing only special characters produce no FTS match — return empty."""
    svc = SearchService(DummyEnv(), DummyCtx())
    repo = DummyRepo()
    repo.articles = ["should_not_appear"]
    svc._repo = repo

    result = await svc.search_articles("!!!", page=1)

    assert result.items == []
    assert result.total == 0
    assert result.has_more is False


# ── SearchService.search_tags ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_tags_returns_matching_tags():
    svc = SearchService(DummyEnv(), DummyCtx())
    repo = DummyRepo()
    repo.tags = [make_tag("python"), make_tag("pytorch")]
    repo.tags_count = 2
    svc._repo = repo

    result = await svc.search_tags("pyth", page=1)

    assert len(result.items) == 2
    assert result.total == 2
    assert result.has_more is False


@pytest.mark.asyncio
async def test_search_tags_pagination():
    svc = SearchService(DummyEnv(), DummyCtx())
    repo = DummyRepo()
    repo.tags = [make_tag() for _ in range(20)]
    repo.tags_count = 50
    svc._repo = repo

    result = await svc.search_tags("py", page=2)

    assert result.page == 2
    assert result.has_more is True


# ── SearchService.search_authors ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_authors_returns_matching_users():
    svc = SearchService(DummyEnv(), DummyCtx())
    repo = DummyRepo()
    repo.authors = [make_user("Alice"), make_user("Alan")]
    repo.authors_count = 2
    svc._repo = repo

    result = await svc.search_authors("al", page=1)

    assert len(result.items) == 2
    assert result.total == 2


# ── SearchService.search_all ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_all_combines_all_types():
    svc = SearchService(DummyEnv(), DummyCtx())
    repo = DummyRepo()
    repo.articles = ["a1"]
    repo.articles_count = 5
    repo.tags = [make_tag()]
    repo.tags_count = 3
    repo.authors = [make_user()]
    repo.authors_count = 1
    svc._repo = repo

    result = await svc.search_all("python")

    assert result["query"] == "python"
    assert result["articles"]["items"] == ["a1"]
    assert result["articles"]["total"] == 5
    assert len(result["tags"]["items"]) == 1
    assert result["tags"]["total"] == 3
    assert len(result["authors"]["items"]) == 1
    assert result["authors"]["total"] == 1


@pytest.mark.asyncio
async def test_search_all_handles_bad_fts_query():
    """search_all with a special-char-only query returns empty articles, but tags/authors still run."""
    svc = SearchService(DummyEnv(), DummyCtx())
    repo = DummyRepo()
    repo.tags = [make_tag()]
    repo.tags_count = 1
    svc._repo = repo

    result = await svc.search_all("!!!")

    assert result["articles"]["items"] == []
    assert result["articles"]["total"] == 0
    assert result["tags"]["total"] == 1
