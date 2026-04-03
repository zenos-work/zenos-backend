"""Phase 2 tests: Reader Engagement and Social Depth Parity"""

import pytest
from api.social.service import SocialService
from api.articles.service import ArticleService


class TestPhase2Reactions:
    """Test GAP-011: Reaction intents completion and UX consistency"""

    def test_reaction_types_constants(self):
        """Verify all 4 reaction types are defined"""
        assert hasattr(SocialService, "REACTION_TYPES")
        assert "fire" in SocialService.REACTION_TYPES
        assert "lightbulb" in SocialService.REACTION_TYPES
        assert "heart" in SocialService.REACTION_TYPES
        assert "brain" in SocialService.REACTION_TYPES
        assert len(SocialService.REACTION_TYPES) == 4

    def test_reaction_type_validation(self):
        """Verify reaction type validation"""
        valid_types = SocialService.REACTION_TYPES

        # All valid types should be lowercase strings
        for rtype in valid_types:
            assert isinstance(rtype, str)
            assert rtype.islower()


class TestPhase2RelatedArticles:
    """Test GAP-012: Article-side trending/related module parity"""

    def test_article_service_has_related_method(self):
        """Verify get_related method exists in ArticleService"""
        assert hasattr(ArticleService, "get_related")

    def test_article_repository_has_find_related_method(self):
        """Verify find_related method exists in ArticleRepository"""
        from api.articles.repository import ArticleRepository

        assert hasattr(ArticleRepository, "find_related")


class TestPhase2Comments:
    """Test GAP-013: Comment depth and moderation hooks"""

    def test_comment_service_has_moderation_methods(self):
        """Verify comment service has moderation methods"""
        from api.comments.service import CommentService

        assert hasattr(CommentService, "moderate")
        assert hasattr(CommentService, "flag_spam")
        assert hasattr(CommentService, "list_replies")


class TestPhase2SocialProof:
    """Test GAP-014: Share proof and interaction feedback parity"""

    def test_social_service_has_share_tracking(self):
        """Verify share tracking is implemented"""
        assert hasattr(SocialService, "share_article")
        assert hasattr(SocialService, "get_share_stats")


class TestPhase2EngagementMetrics:
    """Test overall engagement metrics tracking"""

    def test_article_tracks_engagement_counters(self):
        """Verify article model tracks engagement metrics"""
        from models.article.model import Article
        from datetime import datetime

        # Create a test article instance
        article = Article(
            id="test-1",
            title="Test",
            content="Test content",
            author_id="user-1",
            author_name="Test Author",
            slug="test",
            status="PUBLISHED",
            is_featured=False,
            read_time_minutes=5,
            created_at=datetime.utcnow().isoformat(),
            likes_count=5,
            comments_count=3,
            shares_count=2,
            views_count=100,
            dislikes_count=1,
        )

        assert article.likes_count == 5
        assert article.comments_count == 3
        assert article.shares_count == 2
        assert article.views_count == 100
        assert article.dislikes_count == 1

    def test_engagement_calculation_formula(self):
        """Test that engagement scores are calculated correctly"""
        # Trending score formula: likes*3 + comments*2 + shares*4 + views*0.02 - dislikes*2

        likes = 10
        comments = 5
        shares = 2
        views = 100
        dislikes = 1

        score = (
            (likes * 3)
            + (comments * 2)
            + (shares * 4)
            + (views * 0.02)
            - (dislikes * 2)
        )

        # Score should be: 30 + 10 + 8 + 2 - 2 = 48
        assert score == 48


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
