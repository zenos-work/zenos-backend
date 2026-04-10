from db.repository import BaseRepository
from api.social import queries as Q
from models.article.model import Article
from models.user.model import User
from models.base import row_get
from utils.helpers import new_id


class SocialRepository(BaseRepository):
    """Handles all database operations for likes, bookmarks, follows."""

    # ── LIKES ──────────────────────────────────────
    async def like(self, user_id: str, article_id: str) -> None:
        await self.execute(Q.INSERT_LIKE, user_id, article_id)

    async def unlike(self, user_id: str, article_id: str) -> None:
        await self.execute(Q.DELETE_LIKE, user_id, article_id)

    async def has_liked(self, user_id: str, article_id: str) -> bool:
        """Check if user has liked an article."""
        row = await self.find_one(Q.SELECT_IF_LIKED, user_id, article_id)
        return bool(row)

    async def count_likes(self, article_id: str) -> int:
        """Count total likes for an article."""
        row = await self.find_one(Q.COUNT_LIKES, article_id)
        return row_get(row, "count", 0) if row else 0

    # ── DISLIKES ───────────────────────────────────
    async def dislike(self, user_id: str, article_id: str) -> None:
        await self.execute(Q.INSERT_DISLIKE, user_id, article_id)

    async def undislike(self, user_id: str, article_id: str) -> None:
        await self.execute(Q.DELETE_DISLIKE, user_id, article_id)

    async def has_disliked(self, user_id: str, article_id: str) -> bool:
        row = await self.find_one(Q.SELECT_IF_DISLIKED, user_id, article_id)
        return bool(row)

    async def count_dislikes(self, article_id: str) -> int:
        row = await self.find_one(Q.COUNT_DISLIKES, article_id)
        return row_get(row, "count", 0) if row else 0

    # ── SHARES ─────────────────────────────────────
    async def share(self, user_id: str, article_id: str, provider: str) -> None:
        await self.execute(Q.INSERT_SHARE, new_id(), user_id, article_id, provider)

    async def count_shares(self, article_id: str) -> int:
        row = await self.find_one(Q.COUNT_SHARES, article_id)
        return row_get(row, "count", 0) if row else 0

    # ── REACTIONS ─────────────────────────────────
    async def add_reaction(
        self, article_id: str, user_id: str, reaction_type: str
    ) -> None:
        await self.execute(Q.INSERT_REACTION, article_id, user_id, reaction_type)

    async def remove_reaction(
        self, article_id: str, user_id: str, reaction_type: str
    ) -> None:
        await self.execute(Q.DELETE_REACTION, article_id, user_id, reaction_type)

    async def has_reacted(
        self, article_id: str, user_id: str, reaction_type: str
    ) -> bool:
        row = await self.find_one(
            Q.SELECT_IF_REACTED, article_id, user_id, reaction_type
        )
        return bool(row)

    async def get_reaction_counts(self, article_id: str) -> dict:
        row = await self.find_one(Q.SELECT_REACTION_COUNTS, article_id)
        if not row:
            return {
                "fire": 0,
                "lightbulb": 0,
                "heart": 0,
                "brain": 0,
            }
        return {
            "fire": int(row_get(row, "fire_count", 0) or 0),
            "lightbulb": int(row_get(row, "lightbulb_count", 0) or 0),
            "heart": int(row_get(row, "heart_count", 0) or 0),
            "brain": int(row_get(row, "brain_count", 0) or 0),
        }

    async def get_user_reactions(self, article_id: str, user_id: str) -> set[str]:
        rows = await self.find_all(Q.SELECT_USER_REACTIONS, article_id, user_id)
        return {
            str(row_get(r, "reaction_type", ""))
            for r in rows
            if row_get(r, "reaction_type")
        }

    # ── BOOKMARKS ──────────────────────────────────
    async def bookmark(self, user_id: str, article_id: str) -> None:
        await self.execute(Q.INSERT_BOOKMARK, user_id, article_id)

    async def unbookmark(self, user_id: str, article_id: str) -> None:
        await self.execute(Q.DELETE_BOOKMARK, user_id, article_id)

    async def has_bookmarked(self, user_id: str, article_id: str) -> bool:
        """Check if user has bookmarked an article."""
        row = await self.find_one(Q.SELECT_IF_BOOKMARKED, user_id, article_id)
        return bool(row)

    async def find_bookmarks(self, user_id: str, limit: int, offset: int) -> list:
        rows = await self.find_all(Q.SELECT_BOOKMARKS_BY_USER, user_id, limit, offset)
        return self.map_many(rows, Article)

    async def count_bookmarks(self, user_id: str) -> int:
        """Count total bookmarks for a user."""
        row = await self.find_one(Q.COUNT_BOOKMARKS, user_id)
        return row_get(row, "count", 0) if row else 0

    # ── FOLLOWS ────────────────────────────────────
    async def follow(
        self, follower_id: str, following_id: str, following_type: str = "user"
    ) -> None:
        await self.execute(
            Q.INSERT_FOLLOW, follower_id, following_id, following_type or ""
        )

    async def unfollow(
        self, follower_id: str, following_id: str, following_type: str = "user"
    ) -> None:
        await self.execute(
            Q.DELETE_FOLLOW, follower_id, following_id, following_type or ""
        )

    async def is_following(
        self, follower_id: str, following_id: str, following_type: str = "user"
    ) -> bool:
        """Check if user is following another entity."""
        row = await self.find_one(
            Q.SELECT_IF_FOLLOWING, follower_id, following_id, following_type or ""
        )
        return bool(row)

    async def find_followers(self, user_id: str, limit: int, offset: int) -> list:
        """Get paginated list of users following a user."""
        rows = await self.find_all(Q.SELECT_FOLLOWERS, user_id, limit, offset)
        return self.map_many(rows, User)

    async def count_followers(self, user_id: str) -> int:
        """Count followers for a user."""
        row = await self.find_one(Q.COUNT_FOLLOWERS, user_id)
        return row_get(row, "count", 0) if row else 0

    async def find_following(self, user_id: str, limit: int, offset: int) -> list:
        """Get paginated list of users that a user is following."""
        rows = await self.find_all(Q.SELECT_FOLLOWING, user_id, limit, offset)
        return self.map_many(rows, User)

    async def count_following(self, user_id: str) -> int:
        """Count users that a user is following."""
        row = await self.find_one(Q.COUNT_FOLLOWING, user_id)
        return row_get(row, "count", 0) if row else 0
