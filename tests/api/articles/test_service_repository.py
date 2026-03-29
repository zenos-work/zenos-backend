import importlib

import pytest

from models.article.model import Article
from models.common.enums import ArticleStatus


ArticleService = importlib.import_module("api.articles.service").ArticleService
ArticleRepository = importlib.import_module("api.articles.repository").ArticleRepository
Q = importlib.import_module("api.articles.queries")


class _Env:
    class DB:
        pass


def _article(id="a1", title="Title", status=ArticleStatus.DRAFT):
    return Article(
        id=id,
        title=title,
        slug="slug",
        status=status,
        author_id="u1",
        views_count=0,
        likes_count=0,
        dislikes_count=0,
        comments_count=0,
        is_featured=0,
        read_time_minutes=1,
        created_at="2026-01-01T00:00:00Z",
        content="x" * 60,
        updated_at="2026-01-01T00:00:00Z",
    )


class _ReqCreate:
    title = "New title"
    subtitle = "sub"
    content_type = "article"
    content = "x" * 80
    cover_image_url = "https://img"
    tag_ids = ["t1", "t2"]
    last_verified_at = None
    expires_at = None
    seo_title = None
    seo_description = None
    canonical_url = None
    og_image_url = None
    seo_schema_type = None


class _ReqUpdate:
    title = "Updated"
    subtitle = "updated-sub"
    content_type = "how-to"
    content = "y" * 90
    cover_image_url = "https://img2"
    tag_ids = ["t3"]
    last_verified_at = None
    expires_at = None
    seo_title = None
    seo_description = None
    canonical_url = None
    og_image_url = None
    seo_schema_type = None


class TestArticleService:
    @pytest.mark.asyncio
    async def test_create_and_update_and_delete(self, monkeypatch):
        svc = ArticleService(_Env())

        class _Repo:
            async def is_valid_content_type(self, _content_type):
                return True

            async def insert(self, *args):
                return _article(id=args[0], title=args[2], status=args[-1])

            async def sync_tags(self, article_id, tag_ids):
                self.sync = (article_id, tag_ids)

            async def _fetch_tags(self, article_id):
                return [{"id": "t1"}]

            async def update(
                self,
                article_id,
                title,
                content,
                subtitle,
                content_type,
                cover,
                read_time,
                last_verified_at=None,
                expires_at=None,
                seo_title=None,
                seo_description=None,
                canonical_url=None,
                og_image_url=None,
                seo_schema_type=None,
            ):
                a = _article(id=article_id, title=title)
                a.subtitle = subtitle
                a.content_type = content_type
                a.cover_image_url = cover
                a.read_time_minutes = read_time
                return a

            async def delete(self, article_id):
                self.deleted = article_id

            async def increment_views(self, article_id):
                self.viewed = article_id

            async def set_status(self, *args, **kwargs):
                self.status_call = (args, kwargs)

        repo = _Repo()
        svc._repo = repo

        monkeypatch.setattr("api.articles.service.new_id", lambda: "aid-1")
        monkeypatch.setattr("api.articles.service.unique_slug", lambda title: "slug-1")
        monkeypatch.setattr("api.articles.service.calc_read_time", lambda content: 7)

        created = await svc.create(_ReqCreate(), author_id="u1")
        assert created.id == "aid-1"
        assert created.slug == "slug"
        assert repo.sync == ("aid-1", ["t1", "t2"])

        current = _article(id="aid-1", title="Current")
        updated = await svc.update("aid-1", _ReqUpdate(), current)
        assert updated.title == "Updated"
        assert repo.sync == ("aid-1", ["t3"])

        await svc.delete("aid-1")
        assert repo.deleted == "aid-1"

        await svc.increment_views("aid-1")
        assert repo.viewed == "aid-1"

    @pytest.mark.asyncio
    async def test_transition_variants_and_unknown(self):
        svc = ArticleService(_Env())

        class _Repo:
            def __init__(self):
                self.calls = []

            async def set_status(self, article_id, status, **kwargs):
                self.calls.append((article_id, status, kwargs))

        repo = _Repo()
        svc._repo = repo

        await svc.transition("a1", ArticleStatus.SUBMITTED)
        await svc.transition("a1", ArticleStatus.APPROVED, actor_id="approver")
        await svc.transition("a1", ArticleStatus.REJECTED, note="bad")
        await svc.transition("a1", ArticleStatus.PUBLISHED)
        await svc.transition("a1", ArticleStatus.ARCHIVED)

        assert repo.calls[0][1] == ArticleStatus.SUBMITTED
        assert repo.calls[1][2]["approved_by"] == "approver"
        assert repo.calls[2][2]["rejection_note"] == "bad"
        assert repo.calls[3][2]["publish"] is True

        with pytest.raises(ValueError, match="Unknown status"):
            await svc.transition("a1", "BOGUS")


class TestArticleRepository:
    @pytest.mark.asyncio
    async def test_find_published_branches_and_find_by_author(self, monkeypatch):
        repo = ArticleRepository.__new__(ArticleRepository)

        calls = []

        async def _find_all(sql, *params):
            calls.append((sql, params))
            return [{"id": "a1"}]

        def _map_many(rows, model_cls):
            return rows

        repo.find_all = _find_all
        repo.map_many = _map_many

        result_tag = await repo.find_published(page=1, limit=10, tag="python")
        result_search = await repo.find_published(page=1, limit=10, search="fintech")
        result_default = await repo.find_published(page=1, limit=10)

        assert result_tag.items == [{"id": "a1"}]
        assert result_search.items == [{"id": "a1"}]
        assert result_default.items == [{"id": "a1"}]
        assert calls[0][0] == Q.SELECT_PUBLISHED_BY_TAG
        assert calls[1][0] == Q.SELECT_PUBLISHED_SEARCH
        assert calls[2][0] == Q.SELECT_PUBLISHED_LIST

        await repo.find_by_author("u1", page=1, limit=10, status="DRAFT")
        await repo.find_by_author("u1", page=1, limit=10)
        assert calls[3][0] == Q.SELECT_BY_AUTHOR_AND_STATUS
        assert calls[4][0] == Q.SELECT_BY_AUTHOR

    @pytest.mark.asyncio
    async def test_find_by_id_or_slug_and_owner_and_fetch_tags(self):
        repo = ArticleRepository.__new__(ArticleRepository)

        async def _find_one(sql, *params):
            if sql == Q.SELECT_BY_ID_OR_SLUG:
                return {
                    "id": "a1",
                    "title": "t",
                    "slug": "s",
                    "status": "DRAFT",
                    "author_id": "u1",
                    "views_count": 0,
                    "likes_count": 0,
                    "comments_count": 0,
                    "is_featured": 0,
                    "read_time_minutes": 1,
                    "created_at": "x",
                    "content": "c",
                    "updated_at": "x",
                }
            if sql == Q.SELECT_AUTHOR_ID_BY_ID:
                return {"author_id": "u1"}
            return None

        async def _find_all(sql, *params):
            if sql == Q.SELECT_TAGS_FOR_ARTICLE:
                return [{"id": "t1", "name": "Tag", "slug": "tag", "article_count": 1}]
            return []

        repo.find_one = _find_one
        repo.find_all = _find_all
        repo.map_one = lambda row, model_cls: model_cls.from_row(row)
        repo.map_many = lambda rows, model_cls: [model_cls.from_row(r) for r in rows]

        article = await repo.find_by_id_or_slug("a1")
        assert article is not None
        assert article.id == "a1"
        assert article.tags[0].id == "t1"

        owner = await repo.find_author_id("a1")
        assert owner == "u1"

    @pytest.mark.asyncio
    async def test_insert_update_set_status_and_counters(self):
        repo = ArticleRepository.__new__(ArticleRepository)

        executed = []

        async def _execute(sql, *params):
            executed.append((sql, params))

        async def _find_one(sql, *params):
            return {
                "id": params[0],
                "title": "t",
                "slug": "s",
                "status": "DRAFT",
                "author_id": "u1",
                "views_count": 0,
                "likes_count": 0,
                "comments_count": 0,
                "is_featured": 0,
                "read_time_minutes": 1,
                "created_at": "x",
                "content": "c",
                "updated_at": "x",
            }

        async def _fetch_tags(_aid):
            return []

        repo.execute = _execute
        repo.find_one = _find_one
        repo.map_one = lambda row, model_cls: model_cls.from_row(row)
        repo._fetch_tags = _fetch_tags

        inserted = await repo.insert(
            "a1",
            "u1",
            "t",
            "slug",
            None,
            "article",
            "c",
            None,
            1,
            "DRAFT",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        updated = await repo.update(
            "a1",
            "t2",
            "c2",
            None,
            "how-to",
            None,
            2,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )

        assert inserted.id == "a1"
        assert updated.id == "a1"
        assert executed[0][1][4] == ""
        assert executed[0][1][5] == "article"
        assert executed[0][1][7] == ""
        assert executed[1][1][2] == ""
        assert executed[1][1][3] == "how-to"
        assert executed[1][1][4] == ""

        await repo.set_status("a1", "APPROVED", approved_by="approver")
        await repo.set_status("a1", "REJECTED", rejection_note="bad")
        await repo.set_status("a1", "PUBLISHED", publish=True)
        await repo.set_status("a1", "ARCHIVED")

        await repo.sync_tags("a1", ["t1", "t2"])
        await repo.increment_views("a1")
        await repo.increment_likes("a1")
        await repo.decrement_likes("a1")
        await repo.increment_shares("a1")
        await repo.increment_comments("a1")
        await repo.insert_notification(
            "n1",
            "u1",
            None,
            "MODERATION_PENDING",
            "a1",
            None,
            "pending review",
        )
        await repo.delete("a1")

        sqls = [s for s, _ in executed]
        assert Q.INSERT_ARTICLE in sqls
        assert Q.UPDATE_ARTICLE in sqls
        assert Q.UPDATE_APPROVE in sqls
        assert Q.UPDATE_REJECT in sqls
        assert Q.UPDATE_PUBLISH in sqls
        assert Q.UPDATE_STATUS in sqls
        assert Q.DELETE_ARTICLE_TAGS in sqls
        assert Q.INSERT_ARTICLE_TAG in sqls
        assert Q.UPDATE_INCREMENT_VIEWS in sqls
        assert Q.UPDATE_INCREMENT_LIKES in sqls
        assert Q.UPDATE_DECREMENT_LIKES in sqls
        assert Q.UPDATE_INCREMENT_SHARES in sqls
        assert Q.UPDATE_INCREMENT_COMMENTS in sqls
        assert Q.INSERT_NOTIFICATION in sqls
        assert Q.DELETE_ARTICLE in sqls
        assert executed[-2][1] == (
            "n1",
            "u1",
            "",
            "MODERATION_PENDING",
            "a1",
            "",
            "pending review",
        )
