import importlib

import pytest

from models.comment.requests import (
    CommentCreateRequest,
    CommentModerateRequest,
    CommentUpdateRequest,
)


CommentService = importlib.import_module("api.comments.service").CommentService
CommentRepository = importlib.import_module("api.comments.repository").CommentRepository
Q = importlib.import_module("api.comments.queries")


class _Env:
    class DB:
        pass


class _Log:
    def __init__(self):
        self.events = []

    async def event(self, name, data=None):
        self.events.append((name, data))


class _Ctx:
    def __init__(self):
        self.log = _Log()


class _Comment:
    def __init__(self, id, article_id="a1", author_id="u1", is_deleted=0, flag_count=0):
        self.id = id
        self.article_id = article_id
        self.author_id = author_id
        self.is_deleted = is_deleted
        self.flag_count = flag_count
        self.replies = []


class TestCommentService:
    @pytest.mark.asyncio
    async def test_list_and_reply_methods(self):
        svc = CommentService(_Env(), _Ctx())

        class _Repo:
            async def find_by_article(self, article_id, limit, offset):
                return [_Comment("c1", article_id=article_id)]

            async def count_by_article(self, article_id):
                return 1

            async def find_replies(self, parent_id):
                return [_Comment("r1", parent_id)]

            async def find_by_id(self, comment_id):
                return _Comment(comment_id)

            async def find_replies_paginated(self, parent_id, limit, offset):
                return [_Comment("r2")]

            async def count_replies(self, parent_id):
                return 1

            async def find_all_for_moderation(self, limit, offset):
                return [_Comment("c2")]

            async def count_all_comments(self):
                return 9

        svc._repo = _Repo()

        comments = await svc.list_for_article("a1", page=1, limit=20)
        tree, total = await svc.list_for_article_with_replies("a1", page=1, limit=20)
        replies, rtotal = await svc.list_replies("c1", page=1, limit=10)
        mod_list, mod_total = await svc.list_all_for_moderation(page=1, limit=10)

        assert len(comments) == 1
        assert total == 1
        assert len(tree[0].replies) == 1
        assert len(replies) == 1
        assert rtotal == 1
        assert len(mod_list) == 1
        assert mod_total == 9

    @pytest.mark.asyncio
    async def test_list_replies_parent_not_found(self):
        svc = CommentService(_Env(), _Ctx())

        class _Repo:
            async def find_by_id(self, comment_id):
                return None

        svc._repo = _Repo()

        with pytest.raises(ValueError, match="Parent comment not found"):
            await svc.list_replies("missing")

    @pytest.mark.asyncio
    async def test_create_update_delete_flag_moderate(self, monkeypatch):
        ctx = _Ctx()
        svc = CommentService(_Env(), ctx)

        class _Repo:
            def __init__(self):
                self.updated = None
                self.deleted = None
                self.flagged = None
                self.moderated = None

            async def insert(self, cid, article_id, author_id, parent_id, content):
                self.inserted = (cid, article_id, author_id, parent_id, content)

            async def find_ownership_row(self, comment_id):
                if comment_id == "missing":
                    return None
                if comment_id == "deleted":
                    return {"author_id": "u1", "is_deleted": 1}
                return {"author_id": "u1", "is_deleted": 0}

            async def update(self, comment_id, content):
                self.updated = (comment_id, content)

            async def find_author_id(self, comment_id):
                if comment_id == "missing":
                    return None
                if comment_id == "foreign":
                    return "u2"
                return "u1"

            async def soft_delete(self, comment_id):
                self.deleted = comment_id

            async def find_by_id(self, comment_id):
                if comment_id == "missing":
                    return None
                return _Comment(comment_id, flag_count=2)

            async def increment_flag_count(self, comment_id):
                self.flagged = comment_id

            async def set_moderation(self, comment_id, is_hidden, reason, moderator_id):
                self.moderated = (comment_id, is_hidden, reason, moderator_id)

        class _ArticleRepo:
            async def increment_comments(self, article_id):
                self.incremented = article_id

        repo = _Repo()
        article_repo = _ArticleRepo()
        svc._repo = repo
        svc._article_repo = article_repo

        monkeypatch.setattr("api.comments.service.new_id", lambda: "cid-1")

        create_req = CommentCreateRequest.from_body(
            {"article_id": "a1", "content": "hello"}
        )
        created_id = await svc.create(create_req, author_id="u1")
        assert created_id == "cid-1"
        assert repo.inserted[0] == "cid-1"
        assert article_repo.incremented == "a1"

        update_req = CommentUpdateRequest.from_body({"content": "updated"})
        await svc.update("c1", update_req, requesting_user_id="u1")
        assert repo.updated == ("c1", "updated")

        with pytest.raises(ValueError, match="Comment not found"):
            await svc.update("missing", update_req, requesting_user_id="u1")

        with pytest.raises(ValueError, match="Cannot edit a deleted comment"):
            await svc.update("deleted", update_req, requesting_user_id="u1")

        with pytest.raises(PermissionError, match="Only the comment author"):
            await svc.update("c1", update_req, requesting_user_id="other")

        await svc.delete("c1", requesting_user_id="u1")
        assert repo.deleted == "c1"

        with pytest.raises(ValueError, match="Comment not found"):
            await svc.delete("missing", requesting_user_id="u1")

        with pytest.raises(PermissionError, match="Forbidden"):
            await svc.delete("foreign", requesting_user_id="u1")

        await svc.delete("foreign", requesting_user_id="u1", is_superadmin=True)
        assert repo.deleted == "foreign"

        await svc.flag_spam("c1", user_id="u9")
        assert repo.flagged == "c1"

        with pytest.raises(ValueError, match="Comment not found"):
            await svc.flag_spam("missing", user_id="u9")

        mod_req = CommentModerateRequest.from_body(
            {"is_hidden": True, "reason": "spam"}
        )
        await svc.moderate("c1", mod_req, moderator_id="mod-1")
        assert repo.moderated == ("c1", True, "spam", "mod-1")

        with pytest.raises(ValueError, match="Comment not found"):
            await svc.moderate("missing", mod_req, moderator_id="mod-1")


class TestCommentRepository:
    @pytest.mark.asyncio
    async def test_read_methods_and_counts(self):
        repo = CommentRepository.__new__(CommentRepository)

        async def _find_one(sql, *params):
            if sql == Q.SELECT_BY_ID:
                if params[0] == "missing":
                    return None
                return {
                    "id": params[0],
                    "article_id": "a1",
                    "author_id": "u1",
                    "is_deleted": 0,
                    "created_at": "2026-01-01T00:00:00Z",
                    "content": "text",
                }
            if sql == Q.COUNT_BY_ARTICLE:
                return {"count": 5}
            if sql == Q.COUNT_REPLIES:
                return {"count": 2}
            if sql == Q.COUNT_ALL_COMMENTS:
                return {"count": 8}
            if sql == Q.SELECT_AUTHOR_BY_ID:
                return {"author_id": "u1", "is_deleted": 0}
            return None

        async def _find_all(sql, *params):
            if sql in (
                Q.SELECT_BY_ARTICLE,
                Q.SELECT_REPLIES_BY_PARENT,
                Q.SELECT_REPLIES_PAGINATED,
                Q.SELECT_FOR_MODERATION,
            ):
                return [
                    {
                        "id": "c1",
                        "article_id": "a1",
                        "author_id": "u1",
                        "is_deleted": 0,
                        "created_at": "2026-01-01T00:00:00Z",
                        "content": "text",
                    }
                ]
            return []

        repo.find_one = _find_one
        repo.find_all = _find_all
        repo.map_one = lambda row, model_cls: model_cls.from_row(row) if row else None
        repo.map_many = lambda rows, model_cls: [model_cls.from_row(r) for r in rows]

        assert (await repo.find_by_id("missing")) is None
        assert (await repo.find_by_id("c1")).id == "c1"
        assert len(await repo.find_by_article("a1", 20, 0)) == 1
        assert await repo.count_by_article("a1") == 5
        assert len(await repo.find_replies("c1")) == 1
        assert len(await repo.find_replies_paginated("c1", 10, 0)) == 1
        assert await repo.count_replies("c1") == 2
        assert len(await repo.find_all_for_moderation(20, 0)) == 1
        assert await repo.count_all_comments() == 8
        assert await repo.find_author_id("c1") == "u1"
        assert await repo.find_ownership_row("c1") == {
            "author_id": "u1",
            "is_deleted": 0,
        }

    @pytest.mark.asyncio
    async def test_write_methods(self):
        repo = CommentRepository.__new__(CommentRepository)
        executed = []

        async def _execute(sql, *params):
            executed.append((sql, params))

        repo.execute = _execute

        await repo.insert("c1", "a1", "u1", None, "hello")
        await repo.update("c1", "edited")
        await repo.soft_delete("c1")
        await repo.increment_flag_count("c1")
        await repo.set_moderation("c1", True, "spam", "mod")

        assert executed[0][0] == Q.INSERT_COMMENT
        assert executed[1][0] == Q.UPDATE_COMMENT
        assert executed[2][0] == Q.SOFT_DELETE
        assert executed[3][0] == Q.INCREMENT_FLAG_COUNT
        assert executed[4][0] == Q.SET_MODERATION
