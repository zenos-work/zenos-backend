import importlib

import pytest


AdminRepository = importlib.import_module("api.admin.repository").AdminRepository
Q = importlib.import_module("api.admin.queries")


class TestAdminRepository:
    @pytest.mark.asyncio
    async def test_count_methods_and_grouped_mappers(self):
        repo = AdminRepository.__new__(AdminRepository)

        async def _find_one(sql, *params):
            mapping = {
                Q.COUNT_ACTIVE_USERS: {"c": 11},
                Q.COUNT_USERS_TOTAL: {"c": 15},
                Q.COUNT_ACTIVE_COMMENTS: {"c": 20},
                Q.COUNT_TOTAL_SHARES: {"c": 44},
                Q.COUNT_PENDING_APPROVALS: {"c": 2},
                Q.COUNT_FLAGGED_COMMENTS: {"c": 3},
                Q.COUNT_HIDDEN_COMMENTS: {"c": 4},
                Q.COUNT_NOTIFICATIONS_LAST_7D: {"c": 5},
                Q.COUNT_PUBLISHED_LAST_7D: {"c": 6},
                Q.COUNT_APPROVED_LAST_7D: {"c": 7},
                Q.COUNT_REJECTED_LAST_7D: {"c": 8},
                Q.COUNT_APPROVAL_QUEUE: {"c": 9},
                Q.COUNT_NOTIFICATIONS_BY_USER: {"c": 10},
            }
            return mapping.get(sql)

        async def _find_all(sql, *params):
            if sql == Q.COUNT_USERS_BY_ROLE:
                return [{"role": "AUTHOR", "c": 7}, {"role": "APPROVER", "c": 2}]
            if sql == Q.COUNT_ARTICLES_BY_STATUS:
                return [{"status": "PUBLISHED", "c": 9}]
            return []

        repo.find_one = _find_one
        repo.find_all = _find_all

        assert await repo.count_active_users() == 11
        assert await repo.count_users_total() == 15
        assert await repo.count_active_comments() == 20
        assert await repo.count_total_shares() == 44
        assert await repo.count_pending_approvals() == 2
        assert await repo.count_flagged_comments() == 3
        assert await repo.count_hidden_comments() == 4
        assert await repo.count_notifications_last_7d() == 5
        assert await repo.count_published_last_7d() == 6
        assert await repo.count_approved_last_7d() == 7
        assert await repo.count_rejected_last_7d() == 8
        assert await repo.count_approval_queue() == 9
        assert await repo.count_notifications("u1") == 10

        users_by_role = await repo.count_users_by_role()
        articles_by_status = await repo.count_articles_by_status()
        assert users_by_role == [
            {"role": "AUTHOR", "c": 7},
            {"role": "APPROVER", "c": 2},
        ]
        assert articles_by_status == [{"status": "PUBLISHED", "c": 9}]

    @pytest.mark.asyncio
    async def test_list_and_mapping_methods(self):
        repo = AdminRepository.__new__(AdminRepository)

        async def _find_all(sql, *params):
            if sql == Q.SELECT_TOP_ARTICLES:
                return [
                    {
                        "id": "a1",
                        "title": "Top",
                        "slug": "top",
                        "status": "PUBLISHED",
                        "author_id": "u1",
                        "views_count": 100,
                        "likes_count": 50,
                        "comments_count": 2,
                        "is_featured": 0,
                        "read_time_minutes": 3,
                        "created_at": "2026-01-01T00:00:00Z",
                    }
                ]
            if sql == Q.SELECT_APPROVAL_QUEUE:
                return [
                    {
                        "id": "a2",
                        "title": "Pending",
                        "slug": "pending",
                        "status": "SUBMITTED",
                        "author_id": "u2",
                        "author_name": "Author",
                        "views_count": 0,
                        "likes_count": 0,
                        "comments_count": 0,
                        "is_featured": 0,
                        "read_time_minutes": 2,
                        "created_at": "2026-01-01T00:00:00Z",
                    }
                ]
            if sql == Q.SELECT_ALL_USERS_ADMIN:
                return [
                    {
                        "id": "u1",
                        "email": "u1@example.com",
                        "name": "User One",
                        "role": "AUTHOR",
                        "is_active": 1,
                        "created_at": "2026-01-01T00:00:00Z",
                        "updated_at": "2026-01-01T00:00:00Z",
                    }
                ]
            if sql == Q.SELECT_NOTIFICATIONS_BY_USER:
                return [
                    {
                        "id": "n1",
                        "type": "APPROVED",
                        "message": "Approved",
                        "is_read": 0,
                        "created_at": "2026-01-01T00:00:00Z",
                        "actor_id": "u2",
                    }
                ]
            return []

        repo.find_all = _find_all
        repo.map_many = lambda rows, model_cls: [model_cls.from_row(r) for r in rows]

        top = await repo.find_top_articles()
        queue = await repo.find_approval_queue(limit=20, offset=0)
        users = await repo.find_all_users(limit=20, offset=0)
        notifications = await repo.find_notifications("u1", limit=20, offset=0)

        assert len(top) == 1
        assert top[0].id == "a1"
        assert len(queue) == 1
        assert queue[0].id == "a2"
        assert len(users) == 1
        assert users[0].id == "u1"
        assert len(notifications) == 1
        assert notifications[0].id == "n1"

    @pytest.mark.asyncio
    async def test_write_methods(self):
        repo = AdminRepository.__new__(AdminRepository)
        executed = []

        async def _execute(sql, *params):
            executed.append((sql, params))

        repo.execute = _execute

        await repo.insert_notification(
            "n1",
            "u1",
            "actor-1",
            "APPROVED",
            "a1",
            "c1",
            "done",
        )
        await repo.mark_notifications_read("u1")
        await repo.mark_notification_read("u1", "n1")

        assert executed[0][0] == Q.INSERT_NOTIFICATION
        assert executed[0][1] == (
            "n1",
            "u1",
            "actor-1",
            "APPROVED",
            "a1",
            "c1",
            "done",
        )
        assert executed[1][0] == Q.UPDATE_MARK_NOTIFICATIONS_READ
        assert executed[1][1] == ("u1",)
        assert executed[2][0] == Q.UPDATE_MARK_NOTIFICATION_READ_BY_ID
        assert executed[2][1] == ("u1", "n1")
