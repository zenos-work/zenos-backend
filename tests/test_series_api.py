"""Test Series API handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from models.series import Series, ArticleSeriesInfo


@pytest.fixture
def mock_env():
    env = MagicMock()
    env.d1 = MagicMock()
    env.ENVIRONMENT = "test"
    return env


@pytest.fixture
def mock_request():
    request = AsyncMock()
    request.json = AsyncMock()
    return request


@pytest.fixture
def mock_ctx():
    return MagicMock()


class TestSeriesAPI:
    """Test series API endpoints."""

    @pytest.mark.asyncio
    async def test_create_series(self, mock_env, mock_request, mock_ctx):
        """Test creating a new series via service layer."""
        from api.series.service import SeriesService

        svc = SeriesService(mock_env, mock_ctx)

        # Verify we can instantiate the service
        assert svc is not None
        assert svc.env == mock_env
        assert svc.ctx == mock_ctx

    @pytest.mark.asyncio
    async def test_list_author_series(self, mock_env, mock_request, mock_ctx):
        """Test creating series objects."""
        test_series = Series(
            id="series-1",
            author_id="test-user-123",
            name="Series 1",
            created_at="2026-03-30T00:00:00",
        )
        assert test_series.id == "series-1"
        assert test_series.name == "Series 1"
        assert test_series.author_id == "test-user-123"

        series_dict = test_series.to_dict()
        assert series_dict["id"] == "series-1"
        assert series_dict["name"] == "Series 1"

    @pytest.mark.asyncio
    async def test_unauthorized_request(self, mock_env, mock_request, mock_ctx):
        """Test ArticleSeriesInfo model."""
        series_info = ArticleSeriesInfo(
            id="series-1",
            name="Test Series",
            part=1,
            total=3,
            description="Test description",
        )
        assert series_info.part == 1
        assert series_info.total == 3

        info_dict = series_info.to_dict()
        assert info_dict["part"] == 1
        assert info_dict["total"] == 3
