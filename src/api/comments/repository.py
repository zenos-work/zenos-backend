from typing import Optional
from db.repository import BaseRepository
from api.comments import queries as Q
from models.comment.model import Comment
from models.base import row_get


class CommentRepository(BaseRepository):
    """Handles all database operations for comments."""

    async def find_by_id(self, comment_id: str) -> Optional[Comment]:
        """Fetch a single comment by ID."""
        row = await self.find_one(Q.SELECT_BY_ID, comment_id)
        if not row:
            return None
        return self.map_one(row, Comment)

    async def find_by_article(self, article_id: str, limit: int, offset: int) -> list:
        """Find top-level comments for an article (not replies)."""
        rows = await self.find_all(Q.SELECT_BY_ARTICLE, article_id, limit, offset)
        return self.map_many(rows, Comment)

    async def count_by_article(self, article_id: str) -> int:
        """Count top-level comments for an article."""
        row = await self.find_one(Q.COUNT_BY_ARTICLE, article_id)
        return row_get(row, "count", 0) if row else 0

    async def find_replies(self, parent_id: str) -> list:
        """Find all (non-paginated) replies to a comment."""
        rows = await self.find_all(Q.SELECT_REPLIES_BY_PARENT, parent_id)
        return self.map_many(rows, Comment)

    async def find_replies_paginated(
        self, parent_id: str, limit: int, offset: int
    ) -> list:
        """Find paginated replies to a comment."""
        rows = await self.find_all(Q.SELECT_REPLIES_PAGINATED, parent_id, limit, offset)
        return self.map_many(rows, Comment)

    async def count_replies(self, parent_id: str) -> int:
        """Count total replies to a comment."""
        row = await self.find_one(Q.COUNT_REPLIES, parent_id)
        return row_get(row, "count", 0) if row else 0

    async def find_all_for_moderation(self, limit: int, offset: int) -> list:
        """Find all comments (including hidden/flagged) for admin moderation."""
        rows = await self.find_all(Q.SELECT_FOR_MODERATION, limit, offset)
        return self.map_many(rows, Comment)

    async def count_all_comments(self) -> int:
        """Count total comments in system."""
        row = await self.find_one(Q.COUNT_ALL_COMMENTS)
        return row_get(row, "count", 0) if row else 0

    async def find_author_id(self, comment_id: str) -> Optional[str]:
        row = await self.find_one(Q.SELECT_AUTHOR_BY_ID, comment_id)
        return row_get(row, "author_id") if row else None

    async def find_ownership_row(self, comment_id: str):
        """Returns author_id + is_deleted for ownership and edit-guard checks."""
        return await self.find_one(Q.SELECT_AUTHOR_BY_ID, comment_id)

    async def insert(
        self,
        cid: str,
        article_id: str,
        author_id: str,
        parent_id: Optional[str],
        content: str,
    ) -> None:
        if parent_id is not None:
            await self.execute(
                Q.INSERT_COMMENT, cid, article_id, author_id, parent_id, content
            )
        else:
            await self.execute(
                Q.INSERT_COMMENT_NO_PARENT, cid, article_id, author_id, content
            )

    async def update(self, comment_id: str, content: str) -> None:
        """
        Update comment content.
        SQL guards: is_deleted = 0 — deleted comments cannot be edited.
        """
        await self.execute(Q.UPDATE_COMMENT, content, comment_id)

    async def soft_delete(self, comment_id: str) -> None:
        """Soft-delete a comment."""
        await self.execute(Q.SOFT_DELETE, comment_id)

    async def increment_flag_count(self, comment_id: str) -> None:
        """Increment spam flag count for a comment."""
        await self.execute(Q.INCREMENT_FLAG_COUNT, comment_id)

    async def set_moderation(
        self,
        comment_id: str,
        is_hidden: bool,
        reason: Optional[str],
        moderator_id: str,
    ) -> None:
        """Set moderation status on a comment."""
        await self.execute(
            Q.SET_MODERATION,
            1 if is_hidden else 0,
            reason,
            moderator_id,
            comment_id,
        )
