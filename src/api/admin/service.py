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

    @staticmethod
    def _default_ranking_weights() -> dict:
        return {
            "likes_weight": 1.0,
            "shares_weight": 2.0,
            "comments_weight": 1.5,
            "dislikes_weight": -1.0,
            "views_weight": 0.1,
            "recency_weight": 0.25,
            "updated_by": None,
            "updated_at": None,
        }

    async def get_stats(self) -> dict:
        total_users = await self._repo.count_active_users()
        users_by_role = await self._repo.count_users_by_role()
        total_comments = await self._repo.count_active_comments()
        total_shares = await self._repo.count_total_shares()
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
            "total_shares": total_shares,
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

    async def mark_notification_read(self, user_id: str, notification_id: str) -> None:
        target = str(notification_id or "").strip()
        if not target:
            raise ValueError("notification_id is required")
        await self._repo.mark_notification_read(user_id, target)

    async def delete_notification(self, user_id: str, notification_id: str) -> None:
        target = str(notification_id or "").strip()
        if not target:
            raise ValueError("notification_id is required")
        await self._repo.delete_notification(user_id, target)

    async def delete_all_notifications(self, user_id: str) -> None:
        await self._repo.delete_all_notifications(user_id)

    async def create_notification(
        self,
        user_id: str,
        type_: str,
        message: str,
        actor_id: str = None,
        article_id: str = None,
        comment_id: str = None,
        channel: str = "in_app",
        group_key: str = None,
    ) -> None:
        await self._repo.insert_notification(
            new_id(),
            user_id,
            actor_id,
            type_,
            article_id,
            comment_id,
            message,
            channel,
            group_key,
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

    async def list_success_signals(self, page: int = 1, limit: int = 25) -> dict:
        page = max(1, page)
        limit = max(1, min(limit, 100))
        offset = (page - 1) * limit

        snapshots = await self._repo.find_success_signals_hourly(limit, offset)
        total = await self._repo.count_success_signals_hourly()

        return {
            "snapshots": snapshots,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit,
                "has_more": page * limit < total,
            },
        }

    async def list_success_signal_history(
        self, article_id: str, hours: int = 24
    ) -> dict:
        article_id = str(article_id or "").strip()
        if not article_id:
            raise ValueError("article_id is required")

        hours = max(1, min(hours, 168))
        points = await self._repo.find_success_signal_history(article_id, hours)
        # Return ascending by hour for easier sparkline plotting.
        points.reverse()
        return {
            "article_id": article_id,
            "hours": hours,
            "points": points,
        }

    async def get_ranking_weights(self) -> dict:
        return await self._repo.get_ranking_weights() or self._default_ranking_weights()

    async def update_ranking_weights(self, payload: dict, actor_id: str) -> dict:
        current = await self.get_ranking_weights()

        def pick(name: str, minimum: float, maximum: float) -> float:
            raw = payload.get(name, current[name])
            try:
                value = float(raw)
            except Exception as exc:
                raise ValueError(f"{name} must be a number") from exc
            if value < minimum or value > maximum:
                raise ValueError(f"{name} must be between {minimum} and {maximum}")
            return value

        likes_weight = pick("likes_weight", -10.0, 10.0)
        shares_weight = pick("shares_weight", -10.0, 10.0)
        comments_weight = pick("comments_weight", -10.0, 10.0)
        dislikes_weight = pick("dislikes_weight", -10.0, 10.0)
        views_weight = pick("views_weight", -1.0, 10.0)
        recency_weight = pick("recency_weight", 0.0, 10.0)

        await self._repo.upsert_ranking_weights(
            likes_weight,
            shares_weight,
            comments_weight,
            dislikes_weight,
            views_weight,
            recency_weight,
            actor_id,
        )
        return {"weights": await self.get_ranking_weights()}

    async def get_rankings(self, limit: int = 10) -> dict:
        safe_limit = max(1, min(int(limit or 10), 50))
        weights = await self.get_ranking_weights()
        by_content_type = await self._repo.find_ranked_content_types(safe_limit)
        top_categories = await self._repo.find_ranked_categories(safe_limit)
        return {
            "weights": weights,
            "content_type_rankings": by_content_type,
            "top_category_rankings": top_categories,
        }

    # ── Notification delivery dispatch ────────────────────────────────────────

    async def get_pending_delivery(self, channel: str, limit: int = 100) -> dict:
        """Fetch notifications with delivery_status='pending' for a given channel.
        For push, also attaches active push_subscriptions per user.
        """
        safe_channel = channel if channel in {"email", "push", "webhook"} else "email"
        safe_limit = max(1, min(int(limit or 100), 500))
        rows = await self._repo.find_pending_delivery_by_channel(
            safe_channel, safe_limit
        )
        if safe_channel == "push" and rows:
            user_ids = list({r["user_id"] for r in rows})
            subs = await self._repo.find_push_subs_for_users(user_ids)
            subs_by_user: dict = {}
            for sub in subs:
                subs_by_user.setdefault(sub["user_id"], []).append(sub)
            for row in rows:
                row["push_subscriptions"] = subs_by_user.get(row["user_id"], [])
        return {"notifications": rows, "count": len(rows), "channel": safe_channel}

    async def bulk_update_delivery_status(self, updates: list[dict]) -> dict:
        """Bulk-update delivery status from the delivery worker callback."""
        succeeded = 0
        failed = 0
        valid_statuses = {"delivered", "failed", "bounced"}
        for update in updates:
            notif_id = str(update.get("id") or "").strip()
            status = str(update.get("status") or "failed").strip()
            external_ref = str(update.get("external_ref") or "").strip()
            if notif_id and status in valid_statuses:
                try:
                    await self._repo.update_notification_delivery_status(
                        notif_id, status, external_ref
                    )
                    succeeded += 1
                except Exception:
                    failed += 1
            else:
                failed += 1
        return {"succeeded": succeeded, "failed": failed, "total": len(updates)}
