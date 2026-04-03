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

    async def count_total_shares(self) -> int:
        row = await self.find_one(Q.COUNT_TOTAL_SHARES)
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
        actor_val = actor_id or ""
        article_val = article_id or ""
        comment_val = comment_id or ""
        await self.execute(
            Q.INSERT_NOTIFICATION,
            nid,
            user_id,
            actor_val,
            type_,
            article_val,
            comment_val,
            message,
        )

    async def mark_notifications_read(self, user_id: str) -> None:
        await self.execute(Q.UPDATE_MARK_NOTIFICATIONS_READ, user_id)

    async def mark_notification_read(self, user_id: str, notification_id: str) -> None:
        await self.execute(
            Q.UPDATE_MARK_NOTIFICATION_READ_BY_ID, user_id, notification_id
        )

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

    async def find_success_signals_hourly(self, limit: int, offset: int) -> list[dict]:
        rows = await self.find_all(Q.SELECT_SUCCESS_SIGNALS_HOURLY, limit, offset)
        return [
            {
                "article_id": row_get(r, "article_id"),
                "slug": row_get(r, "slug"),
                "title": row_get(r, "title"),
                "bucket_hour": row_get(r, "bucket_hour"),
                "views_count": int(row_get(r, "views_count", 0) or 0),
                "likes_count": int(row_get(r, "likes_count", 0) or 0),
                "comments_count": int(row_get(r, "comments_count", 0) or 0),
                "outcome_events_count": int(row_get(r, "outcome_events_count", 0) or 0),
                "outcome_tag_count": int(row_get(r, "outcome_tag_count", 0) or 0),
                "engagement_score": float(row_get(r, "engagement_score", 0) or 0),
                "success_rate": float(row_get(r, "success_rate", 0) or 0),
                "updated_at": row_get(r, "updated_at"),
            }
            for r in rows
        ]

    async def count_success_signals_hourly(self) -> int:
        row = await self.find_one(Q.COUNT_SUCCESS_SIGNALS_HOURLY)
        return row_get(row, "c", 0)

    async def find_success_signal_history(
        self, article_id: str, limit: int
    ) -> list[dict]:
        rows = await self.find_all(
            Q.SELECT_SUCCESS_SIGNAL_HISTORY_BY_ARTICLE,
            article_id,
            limit,
        )
        return [
            {
                "bucket_hour": row_get(r, "bucket_hour"),
                "success_rate": float(row_get(r, "success_rate", 0) or 0),
                "engagement_score": float(row_get(r, "engagement_score", 0) or 0),
            }
            for r in rows
        ]

    async def get_ranking_weights(self) -> Optional[dict]:
        row = await self.find_one(Q.SELECT_RANKING_WEIGHTS)
        if not row:
            return None
        return {
            "likes_weight": float(row_get(row, "likes_weight", 1.0) or 1.0),
            "shares_weight": float(row_get(row, "shares_weight", 2.0) or 2.0),
            "comments_weight": float(row_get(row, "comments_weight", 1.5) or 1.5),
            "dislikes_weight": float(row_get(row, "dislikes_weight", -1.0) or -1.0),
            "views_weight": float(row_get(row, "views_weight", 0.1) or 0.1),
            "recency_weight": float(row_get(row, "recency_weight", 0.25) or 0.25),
            "updated_by": row_get(row, "updated_by"),
            "updated_at": row_get(row, "updated_at"),
        }

    async def upsert_ranking_weights(
        self,
        likes_weight: float,
        shares_weight: float,
        comments_weight: float,
        dislikes_weight: float,
        views_weight: float,
        recency_weight: float,
        updated_by: str,
    ) -> None:
        await self.execute(
            Q.UPSERT_RANKING_WEIGHTS,
            likes_weight,
            shares_weight,
            comments_weight,
            dislikes_weight,
            views_weight,
            recency_weight,
            updated_by,
        )

    async def find_ranked_content_types(self, limit: int) -> list[dict]:
        rows = await self.find_all(Q.SELECT_RANKED_CONTENT_TYPES, limit)
        return [
            {
                "content_type": row_get(r, "content_type"),
                "articles_count": int(row_get(r, "articles_count", 0) or 0),
                "total_score": float(row_get(r, "total_score", 0) or 0),
                "avg_score": float(row_get(r, "avg_score", 0) or 0),
                "likes_count": int(row_get(r, "likes_count", 0) or 0),
                "dislikes_count": int(row_get(r, "dislikes_count", 0) or 0),
                "shares_count": int(row_get(r, "shares_count", 0) or 0),
                "comments_count": int(row_get(r, "comments_count", 0) or 0),
                "views_count": int(row_get(r, "views_count", 0) or 0),
            }
            for r in rows
        ]

    async def find_ranked_categories(self, limit: int) -> list[dict]:
        rows = await self.find_all(Q.SELECT_RANKED_CATEGORIES, limit)
        return [
            {
                "category_slug": row_get(r, "category_slug"),
                "category_name": row_get(r, "category_name"),
                "articles_count": int(row_get(r, "articles_count", 0) or 0),
                "total_score": float(row_get(r, "total_score", 0) or 0),
                "avg_score": float(row_get(r, "avg_score", 0) or 0),
                "likes_count": int(row_get(r, "likes_count", 0) or 0),
                "dislikes_count": int(row_get(r, "dislikes_count", 0) or 0),
                "shares_count": int(row_get(r, "shares_count", 0) or 0),
                "comments_count": int(row_get(r, "comments_count", 0) or 0),
                "views_count": int(row_get(r, "views_count", 0) or 0),
            }
            for r in rows
        ]
