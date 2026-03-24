from typing import Optional
from db.repository import BaseRepository
from api.admin import queries as Q
from models.user.model import User
from models.article.model import Article
from models.notification.model import Notification
from models.base import row_get


class AdminRepository(BaseRepository):
    """Handles all database operations for admin/governance queries."""

    async def count_active_users(self) -> int:
        row = await self.find_one(Q.COUNT_ACTIVE_USERS)
        return row_get(row, "c", 0)

    async def count_users_total(self) -> int:
        row = await self.find_one(Q.COUNT_USERS_TOTAL)
        return row_get(row, "c", 0)

    async def count_users_by_role(self) -> list:
        rows = await self.find_all(Q.COUNT_USERS_BY_ROLE)
        return [
            {
                "role": row_get(r, "role"),
                "c": int(row_get(r, "c", 0) or 0),
            }
            for r in rows
        ]

    async def count_articles_by_status(self) -> list:
        rows = await self.find_all(Q.COUNT_ARTICLES_BY_STATUS)
        return [
            {
                "status": row_get(r, "status"),
                "c": int(row_get(r, "c", 0) or 0),
            }
            for r in rows
        ]

    async def count_active_comments(self) -> int:
        row = await self.find_one(Q.COUNT_ACTIVE_COMMENTS)
        return row_get(row, "c", 0)

    async def count_pending_approvals(self) -> int:
        row = await self.find_one(Q.COUNT_PENDING_APPROVALS)
        return row_get(row, "c", 0)

    async def count_flagged_comments(self) -> int:
        row = await self.find_one(Q.COUNT_FLAGGED_COMMENTS)
        return row_get(row, "c", 0)

    async def count_hidden_comments(self) -> int:
        row = await self.find_one(Q.COUNT_HIDDEN_COMMENTS)
        return row_get(row, "c", 0)

    async def count_notifications_last_7d(self) -> int:
        row = await self.find_one(Q.COUNT_NOTIFICATIONS_LAST_7D)
        return row_get(row, "c", 0)

    async def count_published_last_7d(self) -> int:
        row = await self.find_one(Q.COUNT_PUBLISHED_LAST_7D)
        return row_get(row, "c", 0)

    async def count_approved_last_7d(self) -> int:
        row = await self.find_one(Q.COUNT_APPROVED_LAST_7D)
        return row_get(row, "c", 0)

    async def count_rejected_last_7d(self) -> int:
        row = await self.find_one(Q.COUNT_REJECTED_LAST_7D)
        return row_get(row, "c", 0)

    async def find_top_articles(self) -> list:
        rows = await self.find_all(Q.SELECT_TOP_ARTICLES, "PUBLISHED")
        return self.map_many(rows, Article)

    async def find_approval_queue(self, limit: int, offset: int) -> list:
        rows = await self.find_all(
            Q.SELECT_APPROVAL_QUEUE,
            "SUBMITTED",
            "APPROVED",
            limit,
            offset,
        )
        return self.map_many(rows, Article)

    async def count_approval_queue(self) -> int:
        row = await self.find_one(Q.COUNT_APPROVAL_QUEUE, "SUBMITTED", "APPROVED")
        return row_get(row, "c", 0)

    async def find_all_users(self, limit: int, offset: int) -> list:
        rows = await self.find_all(Q.SELECT_ALL_USERS_ADMIN, limit, offset)
        return self.map_many(rows, User)

    async def find_notifications(self, user_id: str, limit: int, offset: int) -> list:
        rows = await self.find_all(
            Q.SELECT_NOTIFICATIONS_BY_USER, user_id, limit, offset
        )
        return self.map_many(rows, Notification)

    async def count_notifications(self, user_id: str) -> int:
        row = await self.find_one(Q.COUNT_NOTIFICATIONS_BY_USER, user_id)
        return row_get(row, "c", 0)

    async def insert_notification(
        self,
        nid: str,
        user_id: str,
        actor_id: Optional[str],
        type_: str,
        article_id: Optional[str],
        comment_id: Optional[str],
        message: str,
    ) -> None:
        await self.execute(
            Q.INSERT_NOTIFICATION,
            nid,
            user_id,
            actor_id,
            type_,
            article_id,
            comment_id,
            message,
        )

    async def mark_notifications_read(self, user_id: str) -> None:
        await self.execute(Q.UPDATE_MARK_NOTIFICATIONS_READ, user_id)

    async def list_content_types(self) -> list[dict]:
        rows = await self.find_all(Q.SELECT_CONTENT_TYPES_ADMIN)
        return [
            {
                "id": row_get(r, "id"),
                "slug": row_get(r, "slug"),
                "name": row_get(r, "name"),
                "description": row_get(r, "description"),
                "is_active": int(row_get(r, "is_active", 1) or 1),
                "is_system": int(row_get(r, "is_system", 0) or 0),
                "sort_order": int(row_get(r, "sort_order", 100) or 100),
                "created_by": row_get(r, "created_by"),
                "created_at": row_get(r, "created_at"),
                "updated_at": row_get(r, "updated_at"),
            }
            for r in rows
        ]

    async def find_content_type_by_slug(self, slug: str) -> Optional[dict]:
        row = await self.find_one(Q.SELECT_CONTENT_TYPE_BY_SLUG, slug)
        if not row:
            return None
        return {
            "id": row_get(row, "id"),
            "slug": row_get(row, "slug"),
            "name": row_get(row, "name"),
            "description": row_get(row, "description"),
            "is_active": int(row_get(row, "is_active", 1) or 1),
            "is_system": int(row_get(row, "is_system", 0) or 0),
            "sort_order": int(row_get(row, "sort_order", 100) or 100),
            "created_by": row_get(row, "created_by"),
            "created_at": row_get(row, "created_at"),
            "updated_at": row_get(row, "updated_at"),
        }

    async def insert_content_type(
        self,
        content_type_id: str,
        slug: str,
        name: str,
        description: Optional[str],
        sort_order: int,
        created_by: str,
    ) -> None:
        await self.execute(
            Q.INSERT_CONTENT_TYPE,
            content_type_id,
            slug,
            name,
            description,
            sort_order,
            created_by,
        )
