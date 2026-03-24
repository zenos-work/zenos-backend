from api.admin.repository import AdminRepository
from api.users.repository import UserRepository
from models.common.enums import Scope
from utils.helpers import new_id, paginate
import re


class AdminService:
    """Business logic for admin/governance. Zero SQL."""

    def __init__(self, env, ctx=None):
        self._repo = AdminRepository(env.DB, ctx)
        self._user_repo = UserRepository(env.DB, ctx)
        self._ctx = ctx

    async def get_stats(self) -> dict:
        total_users = await self._repo.count_active_users()
        users_by_role = await self._repo.count_users_by_role()
        total_comments = await self._repo.count_active_comments()
        articles_status = await self._repo.count_articles_by_status()
        top_articles = await self._repo.find_top_articles()
        pending_approvals = await self._repo.count_pending_approvals()
        flagged_comments = await self._repo.count_flagged_comments()
        hidden_comments = await self._repo.count_hidden_comments()
        notifications_last_7d = await self._repo.count_notifications_last_7d()
        published_last_7d = await self._repo.count_published_last_7d()
        approved_last_7d = await self._repo.count_approved_last_7d()
        rejected_last_7d = await self._repo.count_rejected_last_7d()
        return {
            "total_users": total_users,
            "total_comments": total_comments,
            "articles_by_status": articles_status,
            "top_articles": [a.to_dict(Scope.LIST) for a in top_articles],
            "governance": {
                "users_by_role": users_by_role,
                "moderation": {
                    "pending_approvals": pending_approvals,
                    "flagged_comments": flagged_comments,
                    "hidden_comments": hidden_comments,
                },
                "recent_activity": {
                    "notifications_7d": notifications_last_7d,
                    "published_7d": published_last_7d,
                    "approved_7d": approved_last_7d,
                    "rejected_7d": rejected_last_7d,
                },
            },
        }

    async def get_approval_queue(self, page: int = 1) -> dict:
        limit, offset = paginate(page, 20)
        articles = await self._repo.find_approval_queue(limit, offset)
        total = await self._repo.count_approval_queue()
        return {
            "queue": [a.to_dict(Scope.ADMIN) for a in articles],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit,
                "has_more": page * limit < total,
            },
        }

    async def list_users(self, page: int = 1) -> dict:
        limit, offset = paginate(page, 50)
        users = await self._repo.find_all_users(limit, offset)
        total = await self._repo.count_users_total()
        return {
            "users": [u.to_dict(Scope.ADMIN) for u in users],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit,
                "has_more": page * limit < total,
            },
        }

    async def ban_user(self, user_id: str) -> None:
        await self._user_repo.ban(user_id)

    async def unban_user(self, user_id: str) -> None:
        await self._user_repo.unban(user_id)

    async def get_notifications(self, user_id: str, page: int = 1) -> dict:
        limit, offset = paginate(page, 30)
        notifications = await self._repo.find_notifications(user_id, limit, offset)
        total = await self._repo.count_notifications(user_id)
        data = [n.to_dict() for n in notifications]
        return {
            "notifications": data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit,
                "has_more": page * limit < total,
            },
        }

    async def mark_notifications_read(self, user_id: str) -> None:
        await self._repo.mark_notifications_read(user_id)

    async def create_notification(
        self,
        user_id: str,
        type_: str,
        message: str,
        actor_id: str = None,
        article_id: str = None,
        comment_id: str = None,
    ) -> None:
        await self._repo.insert_notification(
            new_id(),
            user_id,
            actor_id,
            type_,
            article_id,
            comment_id,
            message,
        )

    async def list_content_types(self) -> dict:
        return {"content_types": await self._repo.list_content_types()}

    async def create_content_type(self, payload: dict, actor_id: str) -> dict:
        name = str(payload.get("name") or "").strip()
        if len(name) < 2:
            raise ValueError("name must be at least 2 characters")
        if len(name) > 80:
            raise ValueError("name cannot exceed 80 characters")

        slug_raw = str(payload.get("slug") or name).strip().lower().replace(" ", "-")
        slug = re.sub(r"[^a-z0-9-]", "", slug_raw)
        slug = re.sub(r"-+", "-", slug).strip("-")
        if not re.match(r"^[a-z0-9][a-z0-9-]{1,49}$", slug):
            raise ValueError(
                "slug must be lowercase letters/numbers with optional hyphens"
            )

        existing = await self._repo.find_content_type_by_slug(slug)
        if existing:
            raise ValueError(f"content type already exists: {slug}")

        description = payload.get("description")
        if description is not None:
            description = str(description).strip()
            if len(description) > 240:
                raise ValueError("description cannot exceed 240 characters")
            if not description:
                description = None

        current = await self._repo.list_content_types()
        sort_order = (
            max((int(ct.get("sort_order", 100) or 100) for ct in current), default=100)
            + 10
        )

        content_type_id = new_id()
        await self._repo.insert_content_type(
            content_type_id,
            slug,
            name,
            description,
            sort_order,
            actor_id,
        )

        created = await self._repo.find_content_type_by_slug(slug)
        return {"content_type": created}
