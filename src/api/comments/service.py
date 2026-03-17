from typing import Optional
from api.comments.repository import CommentRepository
from api.articles.repository import ArticleRepository
from models.comment.model import Comment
from models.comment.requests import (
    CommentCreateRequest,
    CommentUpdateRequest,
    CommentModerateRequest,
)
from models.base import row_get
from utils.helpers import new_id, paginate


class CommentService:
    """Business logic for comments. Zero SQL."""

    def __init__(self, env, ctx=None):
        self._repo = CommentRepository(env.DB, ctx)
        self._article_repo = ArticleRepository(env.DB, ctx)
        self._ctx = ctx

    async def _log(self, name: str, data: dict = None) -> None:
        if self._ctx:
            await self._ctx.log.event(name, data=data)

    async def get_by_id(self, comment_id: str) -> Optional[Comment]:
        """Fetch a single comment by ID."""
        return await self._repo.find_by_id(comment_id)

    async def list_for_article(
        self, article_id: str, page: int = 1, limit: int = 50
    ) -> list:
        _, offset = paginate(page, limit)
        return await self._repo.find_by_article(article_id, limit, offset)

    async def list_for_article_with_replies(
        self, article_id: str, page: int = 1, limit: int = 20
    ) -> tuple:
        """
        List top-level comments for article with full nested reply trees.
        Returns (comments, total_count).
        """
        page = max(1, page)
        limit = max(1, min(limit, 100))
        offset = (page - 1) * limit

        comments = await self._repo.find_by_article(article_id, limit, offset)
        total = await self._repo.count_by_article(article_id)

        # Load nested replies for each top-level comment
        for comment in comments:
            replies = await self._repo.find_replies(comment.id)
            comment.replies = replies

        return comments, total

    async def list_replies(
        self, parent_id: str, page: int = 1, limit: int = 20
    ) -> tuple:
        """
        Lazy-load replies for a comment.
        Returns (replies, total_count).
        """
        page = max(1, page)
        limit = max(1, min(limit, 100))
        offset = (page - 1) * limit

        # Verify parent comment exists
        parent = await self._repo.find_by_id(parent_id)
        if not parent:
            raise ValueError("Parent comment not found")

        replies = await self._repo.find_replies_paginated(parent_id, limit, offset)
        total = await self._repo.count_replies(parent_id)

        return replies, total

    async def list_all_for_moderation(self, page: int = 1, limit: int = 20) -> tuple:
        """
        Admin endpoint: list all comments for moderation.
        Returns (comments, total_count) including flagged/hidden comments.
        """
        page = max(1, page)
        limit = max(1, min(limit, 100))
        offset = (page - 1) * limit

        comments = await self._repo.find_all_for_moderation(limit, offset)
        total = await self._repo.count_all_comments()

        return comments, total

    async def create(self, req: CommentCreateRequest, author_id: str) -> str:
        """Create a new comment or reply."""
        cid = new_id()
        await self._repo.insert(
            cid, req.article_id, author_id, req.parent_id, req.content
        )
        await self._article_repo.increment_comments(req.article_id)
        await self._log(
            "comment.created",
            {
                "comment_id": cid,
                "article_id": req.article_id,
                "author_id": author_id,
                "is_reply": bool(req.parent_id),
            },
        )
        return cid

    async def update(
        self,
        comment_id: str,
        req: CommentUpdateRequest,
        requesting_user_id: str,
    ) -> None:
        """
        Edit a comment's content.

        Rules:
          - Only the comment's own author can edit it.
          - SUPERADMIN cannot edit others' comments (only delete).
          - Deleted (soft-deleted) comments cannot be edited — the SQL
            UPDATE_COMMENT guard (WHERE is_deleted=0) enforces this at DB level.
        """
        row = await self._repo.find_ownership_row(comment_id)
        if not row:
            raise ValueError("Comment not found")
        if row_get(row, "is_deleted", 0):
            raise ValueError("Cannot edit a deleted comment")
        if row_get(row, "author_id") != requesting_user_id:
            raise PermissionError("Only the comment author can edit it")
        await self._repo.update(comment_id, req.content)
        await self._log("comment.updated", {"comment_id": comment_id})

    async def delete(
        self,
        comment_id: str,
        requesting_user_id: str,
        is_superadmin: bool = False,
    ) -> None:
        """Delete (soft-delete) a comment."""
        owner = await self._repo.find_author_id(comment_id)
        if not owner:
            raise ValueError("Comment not found")
        if owner != requesting_user_id and not is_superadmin:
            raise PermissionError("Forbidden")
        await self._repo.soft_delete(comment_id)
        await self._log(
            "comment.deleted",
            {
                "comment_id": comment_id,
                "deleted_by": requesting_user_id,
            },
        )

    async def flag_spam(self, comment_id: str, user_id: str) -> None:
        """Flag a comment as spam/abuse."""
        comment = await self._repo.find_by_id(comment_id)
        if not comment:
            raise ValueError("Comment not found")
        await self._repo.increment_flag_count(comment_id)
        await self._log(
            "comment.flagged",
            {
                "comment_id": comment_id,
                "flagged_by": user_id,
                "new_flag_count": comment.flag_count + 1,
            },
        )

    async def moderate(
        self,
        comment_id: str,
        req: CommentModerateRequest,
        moderator_id: str,
    ) -> None:
        """Admin: hide/unhide a comment with moderation reason."""
        comment = await self._repo.find_by_id(comment_id)
        if not comment:
            raise ValueError("Comment not found")
        await self._repo.set_moderation(
            comment_id, req.is_hidden, req.reason, moderator_id
        )
        await self._log(
            "comment.moderated",
            {
                "comment_id": comment_id,
                "is_hidden": req.is_hidden,
                "reason": req.reason,
                "moderator_id": moderator_id,
            },
        )
