from typing import Tuple, List
from api.social.repository import SocialRepository
from api.articles.repository import ArticleRepository
from api.users.repository import UserRepository
from api.analytics.service import AnalyticsService
from models.social.model import SocialActionResult


class SocialService:
    """Business logic for social actions (likes, bookmarks, follows). Zero SQL."""

    def __init__(self, env, ctx=None):
        self._repo = SocialRepository(env.DB, ctx)
        self._article_repo = ArticleRepository(env.DB, ctx)
        self._user_repo = UserRepository(env.DB, ctx)
        self._analytics_service = AnalyticsService(env, ctx)
        self._ctx = ctx

    async def _analytics(self, name: str, data: dict = None) -> None:
        if self._ctx:
            await self._ctx.log.analytics(name, data=data)

    # ── LIKES ──────────────────────────────────────
    async def toggle_like(
        self, user_id: str, article_id: str, add: bool
    ) -> SocialActionResult:
        """Like or unlike an article."""
        if add:
            try:
                await self._repo.like(user_id, article_id)
                await self._article_repo.increment_likes(article_id)
                try:
                    await self._analytics_service.record_article_event(
                        article_id=article_id,
                        event_type="LIKE",
                        actor_user_id=user_id,
                        event_source="api",
                    )
                except Exception:
                    pass
            except Exception:
                raise ValueError("Already liked")
        else:
            await self._repo.unlike(user_id, article_id)
            await self._article_repo.decrement_likes(article_id)
        await self._analytics(
            "social.liked" if add else "social.unliked",
            {
                "user_id": user_id,
                "article_id": article_id,
            },
        )
        return SocialActionResult(action="like", target_id=article_id, active=add)

    async def check_liked(self, user_id: str, article_id: str) -> bool:
        """Check if user has liked an article."""
        return await self._repo.has_liked(user_id, article_id)

    async def get_like_stats(self, article_id: str) -> dict:
        """Get like statistics for an article."""
        like_count = await self._repo.count_likes(article_id)
        return {
            "article_id": article_id,
            "like_count": like_count,
        }

    # ── BOOKMARKS ──────────────────────────────────
    async def toggle_bookmark(
        self, user_id: str, article_id: str, add: bool
    ) -> SocialActionResult:
        """Bookmark or unbookmark an article."""
        if add:
            try:
                await self._repo.bookmark(user_id, article_id)
            except Exception:
                raise ValueError("Already bookmarked")
        else:
            await self._repo.unbookmark(user_id, article_id)
        await self._analytics(
            "social.bookmarked" if add else "social.unbookmarked",
            {
                "user_id": user_id,
                "article_id": article_id,
            },
        )
        return SocialActionResult(action="bookmark", target_id=article_id, active=add)

    async def check_bookmarked(self, user_id: str, article_id: str) -> bool:
        """Check if user has bookmarked an article."""
        return await self._repo.has_bookmarked(user_id, article_id)

    async def get_bookmarks(
        self, user_id: str, page: int = 1, limit: int = 20
    ) -> Tuple[List, int]:
        """Get user's bookmarked articles with pagination."""
        page = max(1, page)
        limit = max(1, min(limit, 100))
        offset = (page - 1) * limit
        articles = await self._repo.find_bookmarks(user_id, limit, offset)
        total = await self._repo.count_bookmarks(user_id)
        return articles, total

    # ── FOLLOWS ────────────────────────────────────
    async def toggle_follow(
        self, follower_id: str, following_id: str, add: bool
    ) -> SocialActionResult:
        """Follow or unfollow a user."""
        if follower_id == following_id:
            raise ValueError("Cannot follow yourself")
        if add:
            try:
                await self._repo.follow(follower_id, following_id)
            except Exception:
                raise ValueError("Already following")
        else:
            await self._repo.unfollow(follower_id, following_id)
        await self._analytics(
            "social.followed" if add else "social.unfollowed",
            {
                "follower_id": follower_id,
                "following_id": following_id,
            },
        )
        return SocialActionResult(action="follow", target_id=following_id, active=add)

    async def check_following(self, follower_id: str, following_id: str) -> bool:
        """Check if user is following another user."""
        return await self._repo.is_following(follower_id, following_id)

    async def list_followers(
        self, user_id: str, page: int = 1, limit: int = 20
    ) -> Tuple[List, int]:
        """Get list of users following a user with pagination."""
        page = max(1, page)
        limit = max(1, min(limit, 100))
        offset = (page - 1) * limit
        followers = await self._repo.find_followers(user_id, limit, offset)
        total = await self._repo.count_followers(user_id)
        return followers, total

    async def list_following(
        self, user_id: str, page: int = 1, limit: int = 20
    ) -> Tuple[List, int]:
        """Get list of users that a user is following with pagination."""
        page = max(1, page)
        limit = max(1, min(limit, 100))
        offset = (page - 1) * limit
        following = await self._repo.find_following(user_id, limit, offset)
        total = await self._repo.count_following(user_id)
        return following, total

    # ── STATS ──────────────────────────────────────
    async def get_user_social_stats(self, user_id: str) -> dict:
        """Get comprehensive social statistics for a user."""
        followers_count = await self._repo.count_followers(user_id)
        following_count = await self._repo.count_following(user_id)

        return {
            "user_id": user_id,
            "followers_count": followers_count,
            "following_count": following_count,
        }
