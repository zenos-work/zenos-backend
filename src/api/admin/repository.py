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

    async def count_articles_by_status(self) -> list:
        return await self.find_all(Q.COUNT_ARTICLES_BY_STATUS)

    async def count_active_comments(self) -> int:
        row = await self.find_one(Q.COUNT_ACTIVE_COMMENTS)
        return row_get(row, "c", 0)

    async def find_top_articles(self) -> list:
        rows = await self.find_all(Q.SELECT_TOP_ARTICLES, "PUBLISHED")
        return self.map_many(rows, Article)

    async def find_approval_queue(self) -> list:
        rows = await self.find_all(Q.SELECT_APPROVAL_QUEUE, "SUBMITTED")
        return self.map_many(rows, Article)

    async def find_all_users(self, limit: int, offset: int) -> list:
        rows = await self.find_all(Q.SELECT_ALL_USERS_ADMIN, limit, offset)
        return self.map_many(rows, User)

    async def find_notifications(self, user_id: str, limit: int, offset: int) -> list:
        rows = await self.find_all(
            Q.SELECT_NOTIFICATIONS_BY_USER, user_id, limit, offset
        )
        return self.map_many(rows, Notification)

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
