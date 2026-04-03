"""
Phase 3 Tests: Premium Paywall and Membership (GAP-015, GAP-016, GAP-017)
Comprehensive smoke, regression, and E2E tests for premium article access control,
membership-tracking, and conversion funnel events.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from api.membership.service import MembershipService
from models.article.model import Article
from models.article.requests import ArticleCreateRequest, ArticleUpdateRequest
from models.user.model import User
from datetime import datetime, timedelta


# ─── Fixtures ──────────────────────────────────────────────────


@pytest.fixture
def mock_env():
    """Mock Cloudflare Worker environment."""
    env = MagicMock()
    db_mock = MagicMock()
    db_mock.prepare = MagicMock(return_value=MagicMock())
    db_mock.prepare.return_value.bind = MagicMock(return_value=MagicMock())
    # Ensure all methods are AsyncMock so they can be awaited
    db_mock.prepare.return_value.bind.return_value.first = AsyncMock()
    db_mock.prepare.return_value.bind.return_value.all = AsyncMock()
    db_mock.prepare.return_value.bind.return_value.run = AsyncMock()
    env.DB = db_mock
    env.ENVIRONMENT = "test"
    return env


@pytest.fixture
def mock_ctx():
    """Mock execution context with logging."""
    ctx = MagicMock()
    ctx.logger = MagicMock()
    ctx.trace_id = "test-trace-001"
    return ctx


@pytest.fixture
def sample_user_free():
    """Free tier user (no premium access)."""
    return {
        "sub": "user-free-001",
        "email": "free@example.com",
        "name": "Free User",
    }


@pytest.fixture
def sample_user_premium():
    """Premium tier user (creator_pro)."""
    return {
        "sub": "user-premium-001",
        "email": "premium@example.com",
        "name": "Premium User",
    }


@pytest.fixture
def sample_article_free():
    """Free-to-read article (no premium paywall)."""
    return Article(
        id="art-free-001",
        title="Free Article",
        slug="free-article",
        status="PUBLISHED",
        author_id="author-001",
        views_count=100,
        likes_count=10,
        dislikes_count=1,
        comments_count=3,
        is_featured=0,
        read_time_minutes=5,
        created_at="2026-03-25 10:00:00",
        content="Some free content",
        premium_only=0,
        premium_teaser_words=300,
    )


@pytest.fixture
def sample_article_premium():
    """Premium-only article (requires membership)."""
    return Article(
        id="art-premium-001",
        title="Premium Article",
        slug="premium-article",
        status="PUBLISHED",
        author_id="author-002",
        views_count=50,
        likes_count=20,
        dislikes_count=0,
        comments_count=5,
        is_featured=1,
        read_time_minutes=10,
        created_at="2026-03-24 10:00:00",
        content="Exclusive premium content for members",
        premium_only=1,
        premium_teaser_words=250,
    )


# ─── Unit Tests: Membership Service ────────────────────────────


class TestMembershipService:
    """Test membership service (paywall, tracking, events)."""

    @pytest.mark.asyncio
    async def test_can_read_premium_article_free_user(
        self, mock_env, mock_ctx, sample_user_free
    ):
        """Free user cannot read premium articles."""
        service = MembershipService(mock_env, mock_ctx)

        mock_env.DB.first = AsyncMock(
            return_value={
                "membership_status": "inactive",
                "subscription_expires_at": None,
            }
        )

        result = await service.can_read_premium_article(
            sample_user_free["sub"], "art-premium-001"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_can_read_premium_article_premium_user(
        self, mock_env, mock_ctx, sample_user_premium
    ):
        """Premium user can read premium articles."""
        service = MembershipService(mock_env, mock_ctx)

        expires = (datetime.utcnow() + timedelta(days=30)).isoformat()

        mock_env.DB.first = AsyncMock(
            return_value={
                "membership_status": "active",
                "subscription_expires_at": expires,
            }
        )

        result = await service.can_read_premium_article(
            sample_user_premium["sub"], "art-premium-001"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_can_publish_premium_article_free_user(
        self, mock_env, mock_ctx, sample_user_free
    ):
        """Free user cannot publish premium articles."""
        service = MembershipService(mock_env, mock_ctx)

        mock_env.DB.first = AsyncMock(return_value={"membership_tier": "free"})

        result = await service.can_publish_premium_article(sample_user_free["sub"])
        assert result is False

    @pytest.mark.asyncio
    async def test_can_publish_premium_article_creator_pro(self, mock_env, mock_ctx):
        """Creator Pro user can publish premium articles."""
        service = MembershipService(mock_env, mock_ctx)

        mock_env.DB.first = AsyncMock(return_value={"membership_tier": "creator_pro"})

        result = await service.can_publish_premium_article("user-creator-001")
        assert result is True

    @pytest.mark.asyncio
    async def test_track_premium_read(self, mock_env, mock_ctx, sample_user_premium):
        """Track premium article read event."""
        service = MembershipService(mock_env, mock_ctx)

        mock_env.DB.run = AsyncMock()

        result = await service.track_premium_read(
            user_id=sample_user_premium["sub"],
            article_id="art-premium-001",
            scroll_depth=85.5,
            duration_seconds=300,
        )

        assert result is not None
        assert result["tracked_at"] is not None
        mock_env.DB.run.assert_called()

    @pytest.mark.asyncio
    async def test_log_premium_funnel_event(self, mock_env, mock_ctx):
        """Log premium conversion funnel event."""
        service = MembershipService(mock_env, mock_ctx)

        mock_env.DB.run = AsyncMock()

        result = await service.log_premium_funnel_event(
            event_type="paywall_shown",
            article_id="art-premium-001",
            user_id="user-free-001",
            device_type="mobile",
            referrer="https://medium.com",
        )

        assert result is not None
        assert result["event_id"] is not None
        assert result["logged_at"] is not None
        mock_env.DB.run.assert_called()

    @pytest.mark.asyncio
    async def test_get_membership_plans(self, mock_env, mock_ctx):
        """Retrieve all membership plans."""
        service = MembershipService(mock_env, mock_ctx)

        mock_env.DB.all = AsyncMock(
            return_value=[
                {
                    "id": "plan-free",
                    "name": "Starter",
                    "tier": "free",
                    "price_monthly": 0,
                    "features": '["Rich editor"]',
                },
                {
                    "id": "plan-pro",
                    "name": "Creator Pro",
                    "tier": "creator_pro",
                    "price_monthly": 0,
                    "features": '["Everything in Starter"]',
                },
            ]
        )

        plans = await service.get_membership_plans()
        assert len(plans) == 2
        assert plans[0]["tier"] == "free"
        assert plans[1]["tier"] == "creator_pro"

    @pytest.mark.asyncio
    async def test_upgrade_membership(self, mock_env, mock_ctx):
        """Upgrade user membership to premium tier."""
        service = MembershipService(mock_env, mock_ctx)

        mock_env.DB.run = AsyncMock()

        result = await service.upgrade_membership(
            user_id="user-free-001",
            new_tier="creator_pro",
            stripe_subscription_id="sub_123456",
        )

        assert result is not None
        assert result["tier"] == "creator_pro"
        assert result["status"] == "active"
        mock_env.DB.run.assert_called()

    @pytest.mark.asyncio
    async def test_expired_membership(self, mock_env, mock_ctx):
        """Expired membership should not allow premium access."""
        service = MembershipService(mock_env, mock_ctx)

        # Set expiration in the past
        expired_date = (datetime.utcnow() - timedelta(days=1)).isoformat()

        mock_env.DB.first = AsyncMock(
            return_value={
                "membership_status": "active",
                "subscription_expires_at": expired_date,
            }
        )

        result = await service.can_read_premium_article("user-001", "art-premium-001")
        assert result is False


# ─── Integration Tests: Article Paywall ────────────────────────


class TestArticlePaywall:
    """Integration tests for premium article paywall enforcement."""

    @pytest.mark.asyncio
    async def test_free_article_no_paywall(
        self, mock_env, mock_ctx, sample_article_free
    ):
        """Free articles should not have paywall."""
        assert sample_article_free.premium_only == 0
        assert sample_article_free.premium_teaser_words == 300

    @pytest.mark.asyncio
    async def test_premium_article_has_paywall(
        self, mock_env, mock_ctx, sample_article_premium
    ):
        """Premium articles should have paywall marker."""
        assert sample_article_premium.premium_only == 1
        assert sample_article_premium.premium_teaser_words == 250

    @pytest.mark.asyncio
    async def test_article_create_with_premium_flag(self, mock_env, mock_ctx):
        """Authors can create articles with premium_only flag."""
        request_data = {
            "title": "Exclusive Content",
            "content": "This is exclusive content for premium members only.",
            "premium_only": 1,
            "premium_teaser_words": 200,
        }

        try:
            req = ArticleCreateRequest.from_body(request_data)
            assert req.premium_only == 1
            assert req.premium_teaser_words == 200
        except ValueError as e:
            pytest.fail(f"Should allow premium_only: {e}")

    @pytest.mark.asyncio
    async def test_article_update_with_premium_flag(self, mock_env, mock_ctx):
        """Authors can update premium_only flag."""
        request_data = {
            "content": "Updated premium content with enough body length to satisfy request validation rules.",
            "premium_only": 1,
        }

        try:
            req = ArticleUpdateRequest.from_body(request_data)
            assert req.premium_only == 1
        except ValueError as e:
            pytest.fail(f"Should allow premium_only update: {e}")

    @pytest.mark.asyncio
    async def test_invalid_premium_teaser_words(self, mock_env, mock_ctx):
        """Invalid premium_teaser_words should be rejected."""
        request_data = {
            "title": "Test Article",
            "content": "Content for testing premium teaser words validation.",
            "premium_teaser_words": 5000,  # Exceeds 2000 limit
        }

        with pytest.raises(ValueError, match="premium_teaser_words must be between"):
            ArticleCreateRequest.from_body(request_data)


# ─── Regression Tests: Existing Functionality ──────────────────


class TestPhase3Regression:
    """Regression tests to ensure Phase 3 doesn't break existing functionality."""

    @pytest.mark.asyncio
    async def test_user_model_backward_compatibility(self):
        """User model should still work without membership fields."""
        user = User(
            id="user-001",
            email="user@example.com",
            name="Test User",
            role="READER",
            is_active=1,
            created_at="2026-03-01 10:00:00",
            updated_at="2026-03-01 10:00:00",
        )

        # Should have default membershipvalues
        assert user.membership_tier == "free"
        assert user.membership_status == "inactive"
        assert user.premium_read_count == 0

    @pytest.mark.asyncio
    async def test_article_model_backward_compatibility(self):
        """Article model should still work without premium fields."""
        article = Article(
            id="art-001",
            title="Test Article",
            slug="test-article",
            status="PUBLISHED",
            author_id="author-001",
            views_count=0,
            likes_count=0,
            dislikes_count=0,
            comments_count=0,
            is_featured=0,
            read_time_minutes=5,
            created_at="2026-03-01 10:00:00",
        )

        # Should have default premium values
        assert article.premium_only == 0
        assert article.premium_teaser_words == 300

    @pytest.mark.asyncio
    async def test_article_create_without_premium_fields(self):
        """Creating articles without premium fields should still work."""
        request_data = {
            "title": "Standard Article",
            "content": "This is a standard article without premium features.",
        }

        try:
            req = ArticleCreateRequest.from_body(request_data)
            assert req.premium_only == 0
            assert req.premium_teaser_words == 300
        except ValueError as e:
            pytest.fail(f"Should allow article creation without premium fields: {e}")


# ─── Smoke Tests: Critical Paths ──────────────────────────────


class TestPhase3SmokePath:
    """Smoke tests for critical Phase 3 functionality."""

    @pytest.mark.asyncio
    async def test_smoke_membership_check_flow(self, mock_env, mock_ctx):
        """Smoke test: Check membership and grant/deny access."""
        service = MembershipService(mock_env, mock_ctx)

        # User without membership
        mock_env.DB.first = AsyncMock(
            return_value={
                "membership_status": "inactive",
                "subscription_expires_at": None,
            }
        )

        can_access = await service.can_read_premium_article("user-free", "art-premium")
        assert can_access is False

    @pytest.mark.asyncio
    async def test_smoke_convert_user_to_premium(self, mock_env, mock_ctx):
        """Smoke test: Convert free user to premium."""
        service = MembershipService(mock_env, mock_ctx)
        mock_env.DB.run = AsyncMock()

        result = await service.upgrade_membership(
            user_id="user-free",
            new_tier="creator_pro",
        )

        assert result["tier"] == "creator_pro"
        assert result["status"] == "active"

    @pytest.mark.asyncio
    async def test_smoke_log_conversion_funnel(self, mock_env, mock_ctx):
        """Smoke test: Log conversion funnel events."""
        service = MembershipService(mock_env, mock_ctx)
        mock_env.DB.run = AsyncMock()

        # Log paywall shown
        event1 = await service.log_premium_funnel_event(
            event_type="paywall_shown",
            article_id="art-1",
            user_id="user-1",
        )
        assert event1["event_id"] is not None

        # Log signup started
        event2 = await service.log_premium_funnel_event(
            event_type="signup_started",
            article_id="art-1",
            user_id="user-1",
        )
        assert event2["event_id"] is not None


# ─── Run Tests ──────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
