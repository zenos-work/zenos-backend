import importlib

import pytest

AdminService = importlib.import_module("api.admin.service").AdminService


class DummyRepo:
    async def count_active_users(self):
        return 12

    async def count_users_total(self):
        return 12

    async def count_users_by_role(self):
        return [{"role": "AUTHOR", "c": 7}, {"role": "APPROVER", "c": 2}]

    async def count_active_comments(self):
        return 30

    async def count_total_shares(self):
        return 22

    async def count_articles_by_status(self):
        return [{"status": "PUBLISHED", "c": 9}]

    async def find_top_articles(self):
        return []

    async def count_pending_approvals(self):
        return 4

    async def count_flagged_comments(self):
        return 3

    async def count_hidden_comments(self):
        return 2

    async def count_notifications_last_7d(self):
        return 15

    async def count_published_last_7d(self):
        return 6

    async def count_approved_last_7d(self):
        return 2

    async def count_rejected_last_7d(self):
        return 1

    async def find_all_users(self, limit, offset):
        return []

    async def count_approval_queue(self):
        return 4

    async def find_approval_queue(self, limit, offset):
        return []

    async def find_notifications(self, user_id, limit, offset):
        return []

    async def count_notifications(self, user_id):
        return 0

    async def mark_notifications_read(self, user_id):
        return None

    async def insert_notification(self, *args, **kwargs):
        return None

    async def list_content_types(self):
        return [
            {
                "id": "ct-1",
                "slug": "article",
                "name": "Article",
                "description": None,
                "is_active": 1,
                "is_system": 1,
                "sort_order": 10,
                "created_by": None,
                "created_at": None,
                "updated_at": None,
            }
        ]

    async def find_content_type_by_slug(self, slug):
        return None

    async def insert_content_type(self, *args, **kwargs):
        return None

    async def find_success_signals_hourly(self, limit, offset):
        return [
            {
                "article_id": "a1",
                "slug": "first-post",
                "title": "First Post",
                "bucket_hour": "2026-03-24 12:00:00",
                "views_count": 50,
                "likes_count": 10,
                "comments_count": 4,
                "outcome_events_count": 1,
                "outcome_tag_count": 2,
                "engagement_score": 136.0,
                "success_rate": 68.0,
                "updated_at": "2026-03-24 12:05:00",
            }
        ]

    async def count_success_signals_hourly(self):
        return 1

    async def find_success_signal_history(self, article_id, limit):
        return [
            {
                "bucket_hour": "2026-03-24 12:00:00",
                "success_rate": 50.0,
                "engagement_score": 100.0,
            },
            {
                "bucket_hour": "2026-03-24 11:00:00",
                "success_rate": 25.0,
                "engagement_score": 60.0,
            },
        ]

    async def get_ranking_weights(self):
        return {
            "likes_weight": 1.0,
            "shares_weight": 2.0,
            "comments_weight": 1.5,
            "dislikes_weight": -1.0,
            "views_weight": 0.1,
            "recency_weight": 0.25,
            "updated_by": "u-admin",
            "updated_at": "2026-03-28 10:00:00",
        }

    async def upsert_ranking_weights(
        self,
        likes_weight,
        shares_weight,
        comments_weight,
        dislikes_weight,
        views_weight,
        recency_weight,
        updated_by,
    ):
        return None

    async def find_ranked_content_types(self, limit):
        return [
            {
                "content_type": "article",
                "articles_count": 3,
                "total_score": 240.0,
                "avg_score": 80.0,
                "likes_count": 20,
                "dislikes_count": 2,
                "shares_count": 8,
                "comments_count": 9,
                "views_count": 200,
            }
        ]

    async def find_ranked_categories(self, limit):
        return [
            {
                "category_slug": "fintech",
                "category_name": "Fintech",
                "articles_count": 2,
                "total_score": 180.0,
                "avg_score": 90.0,
                "likes_count": 15,
                "dislikes_count": 1,
                "shares_count": 6,
                "comments_count": 7,
                "views_count": 140,
            }
        ]


class DummyCtx:
    pass


class DummyEnv:
    DB = None


@pytest.mark.asyncio
async def test_get_stats_contains_governance_blocks():
    svc = AdminService(DummyEnv(), DummyCtx())
    svc._repo = DummyRepo()

    stats = await svc.get_stats()

    assert stats["total_users"] == 12
    assert stats["total_comments"] == 30
    assert stats["total_shares"] == 22
    assert "governance" in stats
    assert stats["governance"]["moderation"]["pending_approvals"] == 4
    assert stats["governance"]["moderation"]["flagged_comments"] == 3
    assert stats["governance"]["recent_activity"]["notifications_7d"] == 15


@pytest.mark.asyncio
async def test_list_users_returns_pagination_shape():
    svc = AdminService(DummyEnv(), DummyCtx())
    svc._repo = DummyRepo()

    result = await svc.list_users(page=1)

    assert "users" in result
    assert "pagination" in result
    assert result["pagination"]["total"] == 12
    assert result["pagination"]["has_more"] is False


@pytest.mark.asyncio
async def test_get_notifications_returns_pagination_shape():
    svc = AdminService(DummyEnv(), DummyCtx())
    svc._repo = DummyRepo()

    result = await svc.get_notifications("u1", page=1)

    assert "notifications" in result
    assert "pagination" in result
    assert result["pagination"]["page"] == 1
    assert result["pagination"]["total"] == 0


@pytest.mark.asyncio
async def test_get_approval_queue_returns_pagination_shape():
    svc = AdminService(DummyEnv(), DummyCtx())
    svc._repo = DummyRepo()

    result = await svc.get_approval_queue(page=1)

    assert "queue" in result
    assert "pagination" in result
    assert result["pagination"]["total"] == 4


@pytest.mark.asyncio
async def test_list_content_types_returns_list():
    svc = AdminService(DummyEnv(), DummyCtx())
    svc._repo = DummyRepo()

    result = await svc.list_content_types()

    assert "content_types" in result
    assert isinstance(result["content_types"], list)
    assert result["content_types"][0]["slug"] == "article"


@pytest.mark.asyncio
async def test_create_content_type_success():
    """create_content_type inserts and returns the new content type."""

    class _StatefulRepo(DummyRepo):
        def __init__(self):
            self._store: dict = {}

        async def find_content_type_by_slug(self, slug):
            return self._store.get(slug)

        async def insert_content_type(
            self, ct_id, slug, name, description, sort_order, created_by
        ):
            self._store[slug] = {
                "id": ct_id,
                "slug": slug,
                "name": name,
                "description": description,
                "is_active": 1,
                "is_system": 0,
                "sort_order": sort_order,
                "created_by": created_by,
                "created_at": None,
                "updated_at": None,
            }

    svc = AdminService(DummyEnv(), DummyCtx())
    svc._repo = _StatefulRepo()

    result = await svc.create_content_type({"name": "Deep Dive"}, actor_id="u-admin")

    assert "content_type" in result
    ct = result["content_type"]
    assert ct["name"] == "Deep Dive"
    assert ct["slug"] == "deep-dive"
    assert ct["is_system"] == 0


@pytest.mark.asyncio
async def test_create_content_type_slug_derived_from_name():
    """Slug is auto-derived from name when not provided."""

    class _StatefulRepo(DummyRepo):
        def __init__(self):
            self._store: dict = {}

        async def find_content_type_by_slug(self, slug):
            return self._store.get(slug)

        async def insert_content_type(
            self, ct_id, slug, name, description, sort_order, created_by
        ):
            self._store[slug] = {
                "id": ct_id,
                "slug": slug,
                "name": name,
                "description": description,
                "is_active": 1,
                "is_system": 0,
                "sort_order": sort_order,
                "created_by": created_by,
                "created_at": None,
                "updated_at": None,
            }

    svc = AdminService(DummyEnv(), DummyCtx())
    svc._repo = _StatefulRepo()

    result = await svc.create_content_type({"name": "Opinion Piece"}, actor_id="u1")

    assert result["content_type"]["slug"] == "opinion-piece"


@pytest.mark.asyncio
async def test_create_content_type_rejects_short_name():
    svc = AdminService(DummyEnv(), DummyCtx())
    svc._repo = DummyRepo()

    import pytest as _pytest

    with _pytest.raises(ValueError, match="name must be at least"):
        await svc.create_content_type({"name": "x"}, actor_id="u1")


@pytest.mark.asyncio
async def test_create_content_type_rejects_duplicate_slug():
    """A conflict on an existing slug raises ValueError."""

    class _ConflictRepo(DummyRepo):
        async def find_content_type_by_slug(self, slug):
            return {"id": "ct-existing", "slug": slug, "name": "Existing"}

    svc = AdminService(DummyEnv(), DummyCtx())
    svc._repo = _ConflictRepo()

    import pytest as _pytest

    with _pytest.raises(ValueError, match="content type already exists"):
        await svc.create_content_type({"name": "Article"}, actor_id="u1")


@pytest.mark.asyncio
async def test_list_success_signals_returns_paginated_snapshots():
    svc = AdminService(DummyEnv(), DummyCtx())
    svc._repo = DummyRepo()

    result = await svc.list_success_signals(page=1, limit=25)

    assert "snapshots" in result
    assert len(result["snapshots"]) == 1
    assert result["snapshots"][0]["article_id"] == "a1"
    assert result["pagination"]["total"] == 1
    assert result["pagination"]["has_more"] is False


@pytest.mark.asyncio
async def test_list_success_signal_history_returns_points_in_ascending_order():
    svc = AdminService(DummyEnv(), DummyCtx())
    svc._repo = DummyRepo()

    result = await svc.list_success_signal_history(article_id="a1", hours=24)

    assert result["article_id"] == "a1"
    assert result["hours"] == 24
    assert len(result["points"]) == 2
    assert result["points"][0]["bucket_hour"] == "2026-03-24 11:00:00"
    assert result["points"][1]["bucket_hour"] == "2026-03-24 12:00:00"


@pytest.mark.asyncio
async def test_get_rankings_returns_content_type_and_category_lists():
    svc = AdminService(DummyEnv(), DummyCtx())
    svc._repo = DummyRepo()

    result = await svc.get_rankings(limit=8)

    assert "weights" in result
    assert "content_type_rankings" in result
    assert "top_category_rankings" in result
    assert result["content_type_rankings"][0]["content_type"] == "article"
    assert result["top_category_rankings"][0]["category_slug"] == "fintech"


@pytest.mark.asyncio
async def test_update_ranking_weights_validates_and_returns_saved_weights():
    class _Repo(DummyRepo):
        def __init__(self):
            self.saved = None

        async def upsert_ranking_weights(
            self,
            likes_weight,
            shares_weight,
            comments_weight,
            dislikes_weight,
            views_weight,
            recency_weight,
            updated_by,
        ):
            self.saved = {
                "likes_weight": likes_weight,
                "shares_weight": shares_weight,
                "comments_weight": comments_weight,
                "dislikes_weight": dislikes_weight,
                "views_weight": views_weight,
                "recency_weight": recency_weight,
                "updated_by": updated_by,
            }

        async def get_ranking_weights(self):
            if self.saved:
                return {
                    **self.saved,
                    "updated_at": "2026-03-28 10:01:00",
                }
            return await super().get_ranking_weights()

    svc = AdminService(DummyEnv(), DummyCtx())
    svc._repo = _Repo()

    result = await svc.update_ranking_weights(
        {
            "likes_weight": 1.2,
            "shares_weight": 2.3,
            "comments_weight": 1.7,
            "dislikes_weight": -1.4,
            "views_weight": 0.2,
            "recency_weight": 0.3,
        },
        actor_id="u-admin",
    )

    assert result["weights"]["shares_weight"] == 2.3
    assert result["weights"]["dislikes_weight"] == -1.4


@pytest.mark.asyncio
async def test_update_ranking_weights_rejects_out_of_range_values():
    svc = AdminService(DummyEnv(), DummyCtx())
    svc._repo = DummyRepo()

    import pytest as _pytest

    with _pytest.raises(ValueError, match="likes_weight must be between"):
        await svc.update_ranking_weights({"likes_weight": 99}, actor_id="u-admin")
