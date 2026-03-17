from api.admin.repository import AdminRepository
from api.users.repository import UserRepository
from models.common.enums import Scope
from utils.helpers import new_id, paginate


class AdminService:
    """Business logic for admin/governance. Zero SQL."""

    def __init__(self, env, ctx=None):
        self._repo = AdminRepository(env.DB, ctx)
        self._user_repo = UserRepository(env.DB, ctx)
        self._ctx = ctx

    async def get_stats(self) -> dict:
        total_users = await self._repo.count_active_users()
        total_comments = await self._repo.count_active_comments()
        articles_status = await self._repo.count_articles_by_status()
        top_articles = await self._repo.find_top_articles()
        return {
            "total_users": total_users,
            "total_comments": total_comments,
            "articles_by_status": articles_status,
            "top_articles": [a.to_dict(Scope.LIST) for a in top_articles],
        }

    async def get_approval_queue(self) -> list:
        articles = await self._repo.find_approval_queue()
        return [a.to_dict(Scope.ADMIN) for a in articles]

    async def list_users(self, page: int = 1) -> list:
        limit, offset = paginate(page, 50)
        users = await self._repo.find_all_users(limit, offset)
        return [u.to_dict(Scope.ADMIN) for u in users]

    async def ban_user(self, user_id: str) -> None:
        await self._user_repo.ban(user_id)

    async def unban_user(self, user_id: str) -> None:
        await self._user_repo.unban(user_id)

    async def get_notifications(self, user_id: str, page: int = 1) -> list:
        limit, offset = paginate(page, 30)
        notifications = await self._repo.find_notifications(user_id, limit, offset)
        return [n.to_dict() for n in notifications]

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
