import importlib

import pytest


comments_handler = importlib.import_module("api.comments.handler")


class _Req:
    def __init__(self, method, path, json_body=None):
        self.method = method
        self.url = f"https://test.local{path}"
        self.headers = {}
        self._json = json_body or {}

    async def json(self):
        return self._json


class _Env:
    JWT_SECRET = "x"


class _Ctx:
    trace_id = "trace-1"


class _Item:
    def __init__(self, id):
        self.id = id

    def to_dict(self, scope="default"):
        return {"id": self.id}


class _Svc:
    def __init__(self):
        self.comments = {"c1": _Item("c1")}

    async def list_all_for_moderation(self, page, limit):
        return [_Item("m1")], 1

    async def list_for_article_with_replies(self, article_id, page, limit):
        return [_Item("a1")], 1

    async def create(self, req, author_id):
        if req.content == "bad":
            raise ValueError("bad input")
        return "c1"

    async def get_by_id(self, comment_id):
        return self.comments.get(comment_id)

    async def list_replies(self, parent_id, page, limit):
        if parent_id == "missing":
            raise ValueError("Parent comment not found")
        return [_Item("r1")], 1

    async def update(self, comment_id, req, requesting_user_id):
        if comment_id == "missing":
            raise ValueError("Comment not found")
        if comment_id == "forbidden":
            raise PermissionError("Forbidden")

    async def delete(self, comment_id, requesting_user_id, is_superadmin=False):
        if comment_id == "missing":
            raise ValueError("Comment not found")
        if comment_id == "forbidden" and not is_superadmin:
            raise PermissionError("Forbidden")

    async def flag_spam(self, comment_id, user_id):
        if comment_id == "missing":
            raise ValueError("Comment not found")

    async def moderate(self, comment_id, req, moderator_id):
        if comment_id == "missing":
            raise ValueError("Comment not found")


@pytest.fixture
def svc(monkeypatch):
    s = _Svc()
    monkeypatch.setattr(comments_handler, "CommentService", lambda env, ctx: s)
    return s


class TestCommentHandlerRoutes:
    @pytest.mark.asyncio
    async def test_admin_all_and_missing_article_id(self, monkeypatch, svc):
        async def _user(_request, _env):
            return {"sub": "u1", "role": "APPROVER"}

        monkeypatch.setattr(comments_handler, "get_user", _user)
        monkeypatch.setattr(
            comments_handler, "require_role", lambda user, allowed: True
        )

        admin = await comments_handler.handle_comments(
            _Req("GET", "/api/comments/admin/all?page=1"),
            _Env(),
            "/api/comments/admin/all",
            "GET",
            {"page": ["1"]},
            _Ctx(),
        )
        assert admin.status_code == 200

        missing = await comments_handler.handle_comments(
            _Req("GET", "/api/comments"), _Env(), "/api/comments", "GET", {}, _Ctx()
        )
        assert missing.status_code == 422

    @pytest.mark.asyncio
    async def test_create_and_replies_paths(self, monkeypatch, svc):
        async def _user(_request, _env):
            return {"sub": "u1", "role": "AUTHOR"}

        monkeypatch.setattr(comments_handler, "get_user", _user)
        monkeypatch.setattr(
            comments_handler, "require_role", lambda user, allowed: False
        )

        created = await comments_handler.handle_comments(
            _Req("POST", "/api/comments", {"article_id": "a1", "content": "ok"}),
            _Env(),
            "/api/comments",
            "POST",
            {},
            _Ctx(),
        )
        assert created.status_code == 201

        bad_create = await comments_handler.handle_comments(
            _Req("POST", "/api/comments", {"article_id": "a1", "content": "bad"}),
            _Env(),
            "/api/comments",
            "POST",
            {},
            _Ctx(),
        )
        assert bad_create.status_code == 400

        replies = await comments_handler.handle_comments(
            _Req("GET", "/api/comments/c1/replies?page=1"),
            _Env(),
            "/api/comments/c1/replies",
            "GET",
            {"page": ["1"]},
            _Ctx(),
        )
        assert replies.status_code == 200

        replies_missing = await comments_handler.handle_comments(
            _Req("GET", "/api/comments/missing/replies"),
            _Env(),
            "/api/comments/missing/replies",
            "GET",
            {},
            _Ctx(),
        )
        assert replies_missing.status_code == 404

    @pytest.mark.asyncio
    async def test_update_delete_flag_moderate_and_fallback(self, monkeypatch, svc):
        async def _user(_request, _env):
            return {"sub": "u1", "role": "APPROVER"}

        monkeypatch.setattr(comments_handler, "get_user", _user)
        monkeypatch.setattr(
            comments_handler, "require_role", lambda user, allowed: True
        )

        ok_update = await comments_handler.handle_comments(
            _Req("PUT", "/api/comments/c1", {"content": "x"}),
            _Env(),
            "/api/comments/c1",
            "PUT",
            {},
            _Ctx(),
        )
        assert ok_update.status_code == 200

        not_found_update = await comments_handler.handle_comments(
            _Req("PUT", "/api/comments/missing", {"content": "x"}),
            _Env(),
            "/api/comments/missing",
            "PUT",
            {},
            _Ctx(),
        )
        assert not_found_update.status_code == 404

        forbidden_update = await comments_handler.handle_comments(
            _Req("PUT", "/api/comments/forbidden", {"content": "x"}),
            _Env(),
            "/api/comments/forbidden",
            "PUT",
            {},
            _Ctx(),
        )
        assert forbidden_update.status_code == 403

        ok_delete = await comments_handler.handle_comments(
            _Req("DELETE", "/api/comments/c1"),
            _Env(),
            "/api/comments/c1",
            "DELETE",
            {},
            _Ctx(),
        )
        assert ok_delete.status_code == 200

        monkeypatch.setattr(
            comments_handler, "require_role", lambda user, allowed: False
        )
        forbidden_delete = await comments_handler.handle_comments(
            _Req("DELETE", "/api/comments/forbidden"),
            _Env(),
            "/api/comments/forbidden",
            "DELETE",
            {},
            _Ctx(),
        )
        assert forbidden_delete.status_code == 403

        monkeypatch.setattr(
            comments_handler, "require_role", lambda user, allowed: True
        )

        ok_flag = await comments_handler.handle_comments(
            _Req("POST", "/api/comments/c1/flag"),
            _Env(),
            "/api/comments/c1/flag",
            "POST",
            {},
            _Ctx(),
        )
        assert ok_flag.status_code == 200

        missing_flag = await comments_handler.handle_comments(
            _Req("POST", "/api/comments/missing/flag"),
            _Env(),
            "/api/comments/missing/flag",
            "POST",
            {},
            _Ctx(),
        )
        assert missing_flag.status_code == 404

        ok_mod = await comments_handler.handle_comments(
            _Req(
                "PUT",
                "/api/comments/c1/moderate",
                {"is_hidden": True, "reason": "spam"},
            ),
            _Env(),
            "/api/comments/c1/moderate",
            "PUT",
            {},
            _Ctx(),
        )
        assert ok_mod.status_code == 200

        missing_mod = await comments_handler.handle_comments(
            _Req(
                "PUT",
                "/api/comments/missing/moderate",
                {"is_hidden": True, "reason": "spam"},
            ),
            _Env(),
            "/api/comments/missing/moderate",
            "PUT",
            {},
            _Ctx(),
        )
        assert missing_mod.status_code == 404

        unknown = await comments_handler.handle_comments(
            _Req("GET", "/api/comments/unknown/path"),
            _Env(),
            "/api/comments/unknown/path",
            "GET",
            {},
            _Ctx(),
        )
        assert unknown.status_code == 404
