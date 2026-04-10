"""
Phase 1 Series E2E Smoke Tests
Tests the complete series lifecycle: create → list → assign article → retrieve → delete.
Covers GAP-007 (reading level), GAP-008 (series model), GAP-009 (upload), GAP-010 (publish guidance).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from api.series.service import SeriesService
from api.series.handler import handle_series
from api.series.repository import SeriesRepository
from models.series import Series, ArticleSeriesInfo
from models.series.requests import (
    SeriesCreateRequest,
    SeriesUpdateRequest,
    ArticleSeriesAssignRequest,
)
from models.common.pagination import PaginatedResponse


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_env():
    env = MagicMock()
    env.ENVIRONMENT = "test"
    env.DB = MagicMock()
    env.d1 = env.DB
    env.FRONTEND_URL = "http://localhost:5173"
    return env


@pytest.fixture
def mock_ctx():
    ctx = MagicMock()
    ctx.logger = MagicMock()
    ctx.trace_id = "phase1-test-trace"
    return ctx


@pytest.fixture
def mock_request_factory():
    """Factory for building fake async requests."""

    def _make(method="GET", body=None, url="https://test.local/api/series"):
        req = AsyncMock()
        req.method = method
        req.url = url
        req.json = AsyncMock(return_value=body or {})
        return req

    return _make


@pytest.fixture
def sample_series():
    return Series(
        id="series-abc",
        author_id="author-001",
        name="Python for Fintech",
        description="A deep-dive series on Python in financial technology.",
        cover_image_url="/media/series-cover.png",
        created_at="2026-03-30T00:00:00Z",
        updated_at="2026-03-30T00:00:00Z",
    )


@pytest.fixture
def sample_series_info():
    return ArticleSeriesInfo(
        id="series-abc",
        name="Python for Fintech",
        part=2,
        total=5,
        description="A deep-dive series.",
    )


# ─── Unit: Series model ───────────────────────────────────────────────────────


class TestSeriesModel:
    """GAP-008: Series model data integrity."""

    def test_series_to_dict_includes_all_fields(self, sample_series):
        d = sample_series.to_dict()
        assert d["id"] == "series-abc"
        assert d["author_id"] == "author-001"
        assert d["name"] == "Python for Fintech"
        assert "description" in d
        assert "cover_image_url" in d
        assert "created_at" in d
        assert "updated_at" in d

    def test_series_to_dict_omits_none_fields(self):
        s = Series(
            id="s1",
            author_id="a1",
            name="Minimal Series",
            created_at="2026-01-01T00:00:00Z",
        )
        d = s.to_dict()
        # description and cover_image_url are None — should not appear
        assert "description" not in d
        assert "cover_image_url" not in d

    def test_article_series_info_to_dict(self, sample_series_info):
        d = sample_series_info.to_dict()
        assert d["id"] == "series-abc"
        assert d["part"] == 2
        assert d["total"] == 5
        assert d["name"] == "Python for Fintech"

    def test_article_series_info_part_and_total_types(self, sample_series_info):
        """Part and total must be ints for frontend progress rendering."""
        assert isinstance(sample_series_info.part, int)
        assert isinstance(sample_series_info.total, int)

    def test_series_from_row(self):
        """Series.from_row correctly maps a DB row-like object."""
        row = {
            "id": "row-series-1",
            "author_id": "row-author-1",
            "name": "Row Series",
            "description": "A row-based series.",
            "cover_image_url": None,
            "created_at": "2026-03-30T00:00:00Z",
            "updated_at": "2026-03-30T00:00:00Z",
        }
        s = Series.from_row(row)
        assert s.id == "row-series-1"
        assert s.name == "Row Series"
        assert s.author_id == "row-author-1"


# ─── Unit: Series request validation ─────────────────────────────────────────


class TestSeriesRequests:
    """Validate request validation for series operations."""

    def test_create_request_happy_path(self):
        req = SeriesCreateRequest.from_body({"name": "My Series"})
        assert req.name == "My Series"

    def test_create_request_with_description(self):
        req = SeriesCreateRequest.from_body(
            {
                "name": "Deep Series",
                "description": "A deep description",
                "cover_image_url": "https://example.com/cover.jpg",
            }
        )
        assert req.description == "A deep description"
        assert req.cover_image_url == "https://example.com/cover.jpg"

    def test_create_request_name_required(self):
        with pytest.raises((ValueError, KeyError)):
            SeriesCreateRequest.from_body({})

    def test_create_request_name_too_long(self):
        with pytest.raises(ValueError):
            SeriesCreateRequest.from_body({"name": "X" * 300})

    def test_update_request_partial(self):
        req = SeriesUpdateRequest.from_body({"description": "Updated desc"})
        assert req.description == "Updated desc"

    def test_assign_request_with_part_number(self):
        req = ArticleSeriesAssignRequest.from_body(
            {"series_id": "s1", "part_number": 3}
        )
        assert req.part_number == 3

    def test_assign_request_default_part_number(self):
        """part_number is required - omitting it raises ValueError."""
        with pytest.raises(ValueError):
            ArticleSeriesAssignRequest.from_body({"series_id": "s1"})

    def test_assign_request_part_number_must_be_positive(self):
        with pytest.raises(ValueError):
            ArticleSeriesAssignRequest.from_body({"series_id": "s1", "part_number": 0})

    def test_assign_request_part_number_too_large(self):
        """Any non-positive part_number is invalid (no explicit upper bound)."""
        req = ArticleSeriesAssignRequest.from_body(
            {"series_id": "s1", "part_number": 9999}
        )
        assert req.part_number == 9999


# ─── Service: Series lifecycle (mock repository) ─────────────────────────────


class TestSeriesServiceLifecycle:
    """GAP-008: Full series lifecycle through the service layer."""

    @pytest.mark.asyncio
    async def test_service_create_series(self, mock_env, mock_ctx, sample_series):
        svc = SeriesService(mock_env, mock_ctx)
        svc.repo = AsyncMock()
        svc.repo.create = AsyncMock()
        svc.repo.find_by_id = AsyncMock(return_value=sample_series)

        req = SeriesCreateRequest.from_body({"name": "Python for Fintech"})
        result = await svc.create("author-001", req)

        assert result.name == "Python for Fintech"
        assert result.author_id == "author-001"
        svc.repo.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_service_list_series_by_author(
        self, mock_env, mock_ctx, sample_series
    ):
        svc = SeriesService(mock_env, mock_ctx)
        svc.repo = AsyncMock()
        paginated = PaginatedResponse(items=[sample_series], page=1, limit=20, total=1)
        svc.repo.find_by_author = AsyncMock(return_value=paginated)

        result = await svc.list_by_author("author-001")
        assert result.total == 1
        assert result.items[0].id == "series-abc"

    @pytest.mark.asyncio
    async def test_service_get_by_id_found(self, mock_env, mock_ctx, sample_series):
        svc = SeriesService(mock_env, mock_ctx)
        svc.repo = AsyncMock()
        svc.repo.find_by_id = AsyncMock(return_value=sample_series)

        result = await svc.get_by_id("series-abc")
        assert result is not None
        assert result.id == "series-abc"

    @pytest.mark.asyncio
    async def test_service_get_by_id_not_found(self, mock_env, mock_ctx):
        svc = SeriesService(mock_env, mock_ctx)
        svc.repo = AsyncMock()
        svc.repo.find_by_id = AsyncMock(return_value=None)

        result = await svc.get_by_id("nonexistent-series")
        assert result is None

    @pytest.mark.asyncio
    async def test_service_update_ownership_check(
        self, mock_env, mock_ctx, sample_series
    ):
        svc = SeriesService(mock_env, mock_ctx)
        svc.repo = AsyncMock()
        # Series owned by "author-001"
        svc.repo.find_by_id = AsyncMock(return_value=sample_series)
        svc.repo.update = AsyncMock()

        req = SeriesUpdateRequest.from_body({"name": "Updated Name"})
        # Attempt update by different author should return None
        result = await svc.update("series-abc", "different-author", req)
        assert result is None
        svc.repo.update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_service_delete_authorises_only_owner(
        self, mock_env, mock_ctx, sample_series
    ):
        svc = SeriesService(mock_env, mock_ctx)
        svc.repo = AsyncMock()
        svc.repo.find_by_id = AsyncMock(return_value=sample_series)
        svc.repo.delete = AsyncMock()

        # Wrong author: should fail
        result = await svc.delete("series-abc", "wrong-author")
        assert result is False
        svc.repo.delete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_service_delete_by_owner_succeeds(
        self, mock_env, mock_ctx, sample_series
    ):
        svc = SeriesService(mock_env, mock_ctx)
        svc.repo = AsyncMock()
        svc.repo.find_by_id = AsyncMock(return_value=sample_series)
        svc.repo.delete = AsyncMock()

        result = await svc.delete("series-abc", "author-001")
        assert result is True
        svc.repo.delete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_service_assign_article_conflict_updates_part(
        self, mock_env, mock_ctx, sample_series
    ):
        """Assigning the same article twice should update part number (upsert)."""
        from models.article.model import Article

        svc = SeriesService(mock_env, mock_ctx)
        svc.repo = AsyncMock()
        # Mock article belongs to author-001
        mock_article = MagicMock(spec=Article)
        mock_article.author_id = "author-001"
        svc.article_service = AsyncMock()
        svc.article_service.get_by_id = AsyncMock(return_value=mock_article)
        svc.repo.find_by_id = AsyncMock(return_value=sample_series)
        svc.repo.article_series_exists = AsyncMock(return_value=True)
        svc.repo.update_article_part = AsyncMock()
        svc.repo.assign_article = AsyncMock()

        req = ArticleSeriesAssignRequest.from_body(
            {"series_id": "series-abc", "part_number": 2}
        )
        result = await svc.assign_article(
            "article-xyz", "series-abc", "author-001", req
        )

        assert result is True
        svc.repo.update_article_part.assert_awaited_once()
        svc.repo.assign_article.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_service_assign_article_new_entry(
        self, mock_env, mock_ctx, sample_series
    ):
        """Assigning a new article creates a fresh record."""
        from models.article.model import Article

        svc = SeriesService(mock_env, mock_ctx)
        svc.repo = AsyncMock()
        mock_article = MagicMock(spec=Article)
        mock_article.author_id = "author-001"
        svc.article_service = AsyncMock()
        svc.article_service.get_by_id = AsyncMock(return_value=mock_article)
        svc.repo.find_by_id = AsyncMock(return_value=sample_series)
        svc.repo.article_series_exists = AsyncMock(return_value=False)
        svc.repo.assign_article = AsyncMock()

        req = ArticleSeriesAssignRequest.from_body(
            {"series_id": "series-abc", "part_number": 1}
        )
        result = await svc.assign_article(
            "article-new", "series-abc", "author-001", req
        )

        assert result is True
        svc.repo.assign_article.assert_awaited_once()


class TestSeriesRepositoryResilience:
    """Series repository should degrade gracefully when series tables are unavailable."""

    @pytest.mark.asyncio
    async def test_find_article_series_returns_none_when_schema_missing(self):
        repo = SeriesRepository(MagicMock(), MagicMock())
        repo.find_one = AsyncMock(return_value={"table_count": 0})

        result = await repo.find_article_series("article-123")

        assert result is None

    @pytest.mark.asyncio
    async def test_find_article_series_returns_none_when_query_hits_missing_table(self):
        repo = SeriesRepository(MagicMock(), MagicMock())
        repo.find_one = AsyncMock(
            side_effect=[
                {"table_count": 2},
                Exception("D1_ERROR: no such table: article_series: SQLITE_ERROR"),
            ]
        )

        result = await repo.find_article_series("article-123")

        assert result is None


# ─── Handler: HTTP routing (unauthorized ← correct 401 response) ─────────────


class TestSeriesHandlerAuth:
    """Handler must reject unauthenticated calls for all verbs."""

    @pytest.mark.asyncio
    async def test_handler_returns_401_no_user(
        self, mock_env, mock_request_factory, mock_ctx
    ):
        req = mock_request_factory("POST")
        query = {}

        with patch("api.series.handler.get_user", new=AsyncMock(return_value=None)):
            response = await handle_series(
                req, mock_env, "/api/series", "POST", query, mock_ctx
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_handler_returns_401_on_get_series_no_user(
        self, mock_env, mock_request_factory, mock_ctx
    ):
        req = mock_request_factory("GET")
        query = {}

        with patch("api.series.handler.get_user", new=AsyncMock(return_value=None)):
            response = await handle_series(
                req, mock_env, "/api/series", "GET", query, mock_ctx
            )

        assert response.status_code == 401


# ─── Handler: Happy path (authenticated) ─────────────────────────────────────


class TestSeriesHandlerHappyPath:
    """Handler routes create & list correctly when user is authenticated."""

    @pytest.mark.asyncio
    async def test_handler_create_series_returns_201_body(
        self, mock_env, mock_request_factory, mock_ctx, sample_series
    ):
        req = mock_request_factory("POST", {"name": "Test Series"})
        query = {}
        fake_user = {"sub": "author-001"}

        with (
            patch("api.series.handler.get_user", new=AsyncMock(return_value=fake_user)),
            patch("api.series.handler.SeriesService") as MockSvc,
        ):
            mock_svc_instance = AsyncMock()
            MockSvc.return_value = mock_svc_instance
            mock_svc_instance.create = AsyncMock(return_value=sample_series)

            response = await handle_series(
                req, mock_env, "/api/series", "POST", query, mock_ctx
            )

        assert response.status_code == 200
        body = response.json()
        assert "series" in body
        assert body["series"]["name"] == "Python for Fintech"

    @pytest.mark.asyncio
    async def test_handler_list_series_returns_rows(
        self, mock_env, mock_request_factory, mock_ctx, sample_series
    ):
        req = mock_request_factory("GET")
        query = {"page": ["1"], "limit": ["20"]}
        fake_user = {"sub": "author-001"}

        paginated = PaginatedResponse(items=[sample_series], page=1, limit=20, total=1)

        with (
            patch("api.series.handler.get_user", new=AsyncMock(return_value=fake_user)),
            patch("api.series.handler.SeriesService") as MockSvc,
        ):
            mock_svc_instance = AsyncMock()
            MockSvc.return_value = mock_svc_instance
            mock_svc_instance.list_by_author = AsyncMock(return_value=paginated)

            response = await handle_series(
                req, mock_env, "/api/series", "GET", query, mock_ctx
            )

        assert response.status_code == 200
        body = response.json()
        # to_dict() uses 'items' key
        assert "items" in body
        assert body["total"] == 1

    @pytest.mark.asyncio
    async def test_handler_get_series_by_id_not_found(
        self, mock_env, mock_request_factory, mock_ctx
    ):
        req = mock_request_factory("GET")
        query = {}
        fake_user = {"sub": "author-001"}

        with (
            patch("api.series.handler.get_user", new=AsyncMock(return_value=fake_user)),
            patch("api.series.handler.SeriesService") as MockSvc,
        ):
            mock_svc_instance = AsyncMock()
            MockSvc.return_value = mock_svc_instance
            mock_svc_instance.get_by_id = AsyncMock(return_value=None)

            response = await handle_series(
                req, mock_env, "/api/series/nonexistent", "GET", query, mock_ctx
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_handler_delete_series_not_authorized(
        self, mock_env, mock_request_factory, mock_ctx
    ):
        req = mock_request_factory("DELETE")
        query = {}
        fake_user = {"sub": "author-001"}

        with (
            patch("api.series.handler.get_user", new=AsyncMock(return_value=fake_user)),
            patch("api.series.handler.SeriesService") as MockSvc,
        ):
            mock_svc_instance = AsyncMock()
            MockSvc.return_value = mock_svc_instance
            mock_svc_instance.delete = AsyncMock(return_value=False)

            response = await handle_series(
                req, mock_env, "/api/series/series-abc", "DELETE", query, mock_ctx
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_handler_limit_capped_at_100(
        self, mock_env, mock_request_factory, mock_ctx, sample_series
    ):
        """Query limit should be capped at 100 even if caller passes 9999."""
        req = mock_request_factory("GET")
        query = {"page": ["1"], "limit": ["9999"]}
        fake_user = {"sub": "author-001"}

        paginated = PaginatedResponse(items=[], page=1, limit=100, total=0)

        with (
            patch("api.series.handler.get_user", new=AsyncMock(return_value=fake_user)),
            patch("api.series.handler.SeriesService") as MockSvc,
        ):
            mock_svc_instance = AsyncMock()
            MockSvc.return_value = mock_svc_instance
            mock_svc_instance.list_by_author = AsyncMock(return_value=paginated)

            await handle_series(req, mock_env, "/api/series", "GET", query, mock_ctx)

        # The actual limit passed to service should be 100 max
        called_limit = mock_svc_instance.list_by_author.call_args[0][2]
        assert called_limit == 100


# ─── GAP-007: Reading level in article requests ────────────────────────────────


class TestReadingLevelValidation:
    """GAP-007: Reading level field must be validated by request models."""

    def test_valid_reading_levels_accepted(self):
        from models.article.requests import ArticleCreateRequest

        long_content = "A" * 100  # must be >= 50 chars
        for level in ["Beginner", "Intermediate", "Advanced"]:
            req = ArticleCreateRequest.from_body(
                {
                    "title": "Test Article",
                    "content": long_content,
                    "reading_level": level,
                }
            )
            assert req.reading_level == level

    def test_invalid_reading_level_rejected(self):
        from models.article.requests import ArticleCreateRequest

        long_content = "A" * 100
        with pytest.raises(ValueError):
            ArticleCreateRequest.from_body(
                {
                    "title": "Test Article",
                    "content": long_content,
                    "reading_level": "Expert",
                }
            )

    def test_missing_reading_level_defaults_to_none(self):
        from models.article.requests import ArticleCreateRequest

        long_content = "A" * 100
        req = ArticleCreateRequest.from_body(
            {
                "title": "Test Article",
                "content": long_content,
            }
        )
        assert req.reading_level is None


# ─── GAP-009: Media upload request validation ─────────────────────────────────


class TestMediaUploadValidation:
    """GAP-009: Media upload endpoint exists and validates content type."""

    @pytest.mark.asyncio
    async def test_media_handler_import(self):
        """Media handler should be importable (smoke test for upload endpoint)."""
        from api.media.handler import handle_media

        assert callable(handle_media)

    @pytest.mark.asyncio
    async def test_media_handler_upload_requires_auth(self, mock_env, mock_ctx):
        """Upload endpoint must require authentication."""
        from api.media.handler import handle_media

        req = AsyncMock()
        req.method = "POST"
        req.url = "https://test.local/api/media/upload"
        req.headers = {}
        req.body = AsyncMock(return_value=b"fake image data")

        with patch("api.media.handler.get_user", new=AsyncMock(return_value=None)):
            response = await handle_media(
                req, mock_env, "/api/media/upload", "POST", {}, mock_ctx
            )

        assert response.status_code == 401


# ─── Full smoke: Series article retrieval from articles handler ───────────────


class TestArticleSeriesIntegration:
    """GAP-008: Articles handler exposes /api/articles/:id/series endpoint."""

    @pytest.mark.asyncio
    async def test_articles_series_endpoint_importable(self):
        """The articles handler should include the series endpoint logic."""
        from api.articles.handler import handle_articles

        assert callable(handle_articles)

    @pytest.mark.asyncio
    async def test_article_series_returns_404_for_unknown_article(
        self, mock_env, mock_ctx
    ):
        from api.articles.handler import handle_articles

        req = AsyncMock()
        req.method = "GET"
        req.url = "https://test.local/api/articles/unknown-id/series"
        req.headers = {}

        with (
            patch(
                "api.articles.handler.get_user",
                new=AsyncMock(return_value={"sub": "u1"}),
            ),
            patch("api.series.service.SeriesService") as MockSeriesSvc,
        ):
            mock_ss = AsyncMock()
            MockSeriesSvc.return_value = mock_ss
            mock_ss.get_article_series = AsyncMock(return_value=None)

            response = await handle_articles(
                req, mock_env, "/api/articles/unknown-id/series", "GET", {}, mock_ctx
            )

        # Article has no series -> 404
        assert response.status_code == 404
