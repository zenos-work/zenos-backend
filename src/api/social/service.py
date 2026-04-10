from typing import Tuple, List
from api.social.repository import SocialRepository
from api.articles.repository import ArticleRepository
from api.users.repository import UserRepository
from api.analytics.service import AnalyticsService
from models.social.model import SocialActionResult


class SocialService:
    """Business logic for social actions (likes, bookmarks, follows). Zero SQL."""

    REACTION_TYPES = ("fire", "lightbulb", "heart", "brain")
    SHARE_PROVIDERS = ("linkedin", "x", "facebook")

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

    # ── DISLIKES ───────────────────────────────────
    async def toggle_dislike(
        self, user_id: str, article_id: str, add: bool
    ) -> SocialActionResult:
        """Dislike or remove dislike from an article."""
        if add:
            try:
                await self._repo.dislike(user_id, article_id)
                await self._article_repo.increment_dislikes(article_id)
            except Exception:
                raise ValueError("Already disliked")
        else:
            await self._repo.undislike(user_id, article_id)
            await self._article_repo.decrement_dislikes(article_id)

        await self._analytics(
            "social.disliked" if add else "social.undisliked",
            {
                "user_id": user_id,
                "article_id": article_id,
            },
        )
        return SocialActionResult(action="dislike", target_id=article_id, active=add)

    async def check_disliked(self, user_id: str, article_id: str) -> bool:
        return await self._repo.has_disliked(user_id, article_id)

    async def get_dislike_stats(self, article_id: str) -> dict:
        dislike_count = await self._repo.count_dislikes(article_id)
        return {
            "article_id": article_id,
            "dislike_count": dislike_count,
        }

    # ── SHARES ─────────────────────────────────────
    async def share_article(
        self, user_id: str, article_id: str, provider: str = "linkedin"
    ) -> dict:
        provider_name = str(provider or "linkedin").strip().lower()
        if provider_name not in self.SHARE_PROVIDERS:
            raise ValueError("Unsupported provider")

        await self._repo.share(user_id, article_id, provider_name)
        await self._article_repo.increment_shares(article_id)
        await self._analytics(
            "social.shared",
            {
                "user_id": user_id,
                "article_id": article_id,
                "provider": provider_name,
            },
        )
        share_count = await self._repo.count_shares(article_id)
        return {
            "article_id": article_id,
            "provider": provider_name,
            "share_count": share_count,
        }

    async def get_share_stats(self, article_id: str) -> dict:
        share_count = await self._repo.count_shares(article_id)
        return {
            "article_id": article_id,
            "share_count": share_count,
        }

    # ── REACTIONS ─────────────────────────────────
    async def toggle_reaction(
        self, user_id: str, article_id: str, reaction_type: str
    ) -> SocialActionResult:
        reaction = str(reaction_type or "").strip().lower()
        if reaction not in self.REACTION_TYPES:
            raise ValueError("Invalid reaction type")

        already = await self._repo.has_reacted(article_id, user_id, reaction)
        if already:
            await self._repo.remove_reaction(article_id, user_id, reaction)
            active = False
        else:
            await self._repo.add_reaction(article_id, user_id, reaction)
            active = True

        await self._analytics(
            "social.reacted",
            {
                "user_id": user_id,
                "article_id": article_id,
                "reaction_type": reaction,
                "active": active,
            },
        )
        return SocialActionResult(
            action=f"reaction:{reaction}",
            target_id=article_id,
            active=active,
        )

    async def remove_reaction(
        self, user_id: str, article_id: str, reaction_type: str
    ) -> SocialActionResult:
        reaction = str(reaction_type or "").strip().lower()
        if reaction not in self.REACTION_TYPES:
            raise ValueError("Invalid reaction type")

        await self._repo.remove_reaction(article_id, user_id, reaction)
        await self._analytics(
            "social.reaction_removed",
            {
                "user_id": user_id,
                "article_id": article_id,
                "reaction_type": reaction,
            },
        )
        return SocialActionResult(
            action=f"reaction:{reaction}",
            target_id=article_id,
            active=False,
        )

    async def get_reactions(self, article_id: str, user_id: str | None = None) -> dict:
        counts = await self._repo.get_reaction_counts(article_id)
        reacted = (
            await self._repo.get_user_reactions(article_id, user_id)
            if user_id
            else set()
        )
        reactions = {
            reaction: {
                "count": int(counts.get(reaction, 0) or 0),
                "userReacted": reaction in reacted,
            }
            for reaction in self.REACTION_TYPES
        }
        return {
            "article_id": article_id,
            "reactions": reactions,
            "total_reactions": sum(item["count"] for item in reactions.values()),
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
        self,
        follower_id: str,
        following_id: str,
        add: bool,
        following_type: str = "user",
    ) -> SocialActionResult:
        """Follow or unfollow a user/tag/series."""
        if following_type == "user" and follower_id == following_id:
            raise ValueError("Cannot follow yourself")
        if add:
            try:
                await self._repo.follow(follower_id, following_id, following_type)
            except Exception:
                raise ValueError("Already following")
        else:
            await self._repo.unfollow(follower_id, following_id, following_type)
        await self._analytics(
            "social.followed" if add else "social.unfollowed",
            {
                "follower_id": follower_id,
                "following_id": following_id,
                "following_type": following_type,
            },
        )
        return SocialActionResult(action="follow", target_id=following_id, active=add)

    async def check_following(
        self, follower_id: str, following_id: str, following_type: str = "user"
    ) -> bool:
        """Check if user is following another entity."""
        return await self._repo.is_following(follower_id, following_id, following_type)

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
