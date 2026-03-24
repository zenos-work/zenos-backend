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
