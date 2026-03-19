"""
Phase 9 – Comment tests.

Covers:
  - CommentCreateRequest validation
  - CommentUpdateRequest validation
  - CommentModerateRequest validation
  - Comments endpoint routes
"""

import asyncio
import importlib
from urllib.parse import parse_qs, urlparse

import pytest

CommentCreateRequest = importlib.import_module(
    "models.comment.requests"
).CommentCreateRequest
CommentUpdateRequest = importlib.import_module(
    "models.comment.requests"
).CommentUpdateRequest
CommentModerateRequest = importlib.import_module(
    "models.comment.requests"
).CommentModerateRequest
Comment = importlib.import_module("models.comment.model").Comment
create_token = importlib.import_module("auth.jwt_handler").create_token
comments_handler = importlib.import_module("api.comments.handler")

_JWT_SECRET = "test-secret"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _make_comment(
    id="c1",
    article_id="art-1",
    author_id="auth-user",
    content="A test comment body.",
    is_deleted=0,
    is_hidden=0,
    parent_id=None,
):
    return Comment(
        id=id,
        article_id=article_id,
        author_id=author_id,
        is_deleted=is_deleted,
        created_at="2026-03-18T10:00:00Z",
        content=content,
        is_hidden=is_hidden,
        parent_id=parent_id,
    )


class FakeRequest:
    def __init__(self, method, url, headers=None, json_body=None):
        self.method = method
        self.url = f"https://testserver{url}"
        self.headers = headers or {}
        self._json_body = json_body

    async def json(self):
        return self._json_body if self._json_body is not None else {}


class FakeCtx:
    trace_id = "test-trace-id"

    class log:
        @staticmethod
        async def event(name, data=None):
            pass


class FakeCommentService:
    def __init__(self, env, ctx=None):
        self._comments = {
            "c1": _make_comment(id="c1", author_id="auth-user"),
            "c2": _make_comment(id="c2", author_id="other-user"),
        }
        self._created = []
        self._deleted = []
        self._moderated = []

    async def list_for_article_with_replies(self, article_id, page, limit):
        comments = [c for c in self._comments.values() if c.article_id == article_id]
        return comments, len(comments)

    async def list_all_for_moderation(self, page, limit):
        comments = list(self._comments.values())
        return comments, len(comments)

    async def list_replies(self, parent_id, page, limit):
        replies = [c for c in self._comments.values() if c.parent_id == parent_id]
        return replies, len(replies)

    async def get_by_id(self, comment_id):
        return self._comments.get(comment_id)

    async def create(self, req, author_id):
        cid = f"c-new-{len(self._created)}"
        c = _make_comment(
            id=cid,
            article_id=req.article_id,
            author_id=author_id,
            content=req.content,
            parent_id=req.parent_id,
        )
        self._comments[cid] = c
        self._created.append(cid)
        return cid

    async def update(self, comment_id, req, requesting_user_id):
        c = self._comments.get(comment_id)
        if not c:
            raise ValueError("Comment not found")
        if c.author_id != requesting_user_id:
            raise PermissionError("Forbidden")
        c.content = req.content

    async def delete(self, comment_id, requesting_user_id, is_admin=False):
        c = self._comments.get(comment_id)
        if not c:
            raise ValueError("Comment not found")
        if not is_admin and c.author_id != requesting_user_id:
            raise PermissionError("Forbidden")
        c.is_deleted = 1
        self._deleted.append(comment_id)

    async def moderate(self, comment_id, req, moderator_id):
        c = self._comments.get(comment_id)
        if not c:
            raise ValueError("Comment not found")
        c.is_hidden = 1 if req.is_hidden else 0
        self._moderated.append(comment_id)
        return c


class CommentsClient:
    def __init__(self, env, svc_instance):
        self.env = env
        self.svc = svc_instance

    def get(self, path, headers=None):
        return self._dispatch("GET", path, headers=headers)

    def post(self, path, headers=None, json=None):
        return self._dispatch("POST", path, headers=headers, json_body=json)

    def put(self, path, headers=None, json=None):
        return self._dispatch("PUT", path, headers=headers, json_body=json)

    def delete(self, path, headers=None, json=None):
        return self._dispatch("DELETE", path, headers=headers, json_body=json)

    def _dispatch(self, method, path, headers=None, json_body=None):
        parsed = urlparse(path)
        request = FakeRequest(
            method=method, url=path, headers=headers or {}, json_body=json_body
        )
        svc = self.svc

        class _Env:
            JWT_SECRET = "test-secret"

        def _make_svc(_env, _ctx=None):
            return svc

        import api.comments.handler as _h

        original = _h.CommentService
        _h.CommentService = _make_svc
        try:
            result = asyncio.run(
                comments_handler.handle_comments(
                    request,
                    _Env(),
                    parsed.path,
                    method,
                    parse_qs(parsed.query),
                    FakeCtx(),
                )
            )
        finally:
            _h.CommentService = original
        return result


def _token(role="AUTHOR", sub="auth-user"):
    return create_token({"sub": sub, "role": role}, _JWT_SECRET)


# ─────────────────────────────────────────────────────────────────────────────
# Model Validation Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestCommentCreateRequest:
    def test_valid_minimal(self):
        req = CommentCreateRequest.from_body(
            {"article_id": "art-1", "content": "Nice article!"}
        )
        assert req.article_id == "art-1"
        assert req.parent_id is None

    def test_valid_with_parent(self):
        req = CommentCreateRequest.from_body(
            {"article_id": "art-1", "content": "Reply here.", "parent_id": "c1"}
        )
        assert req.parent_id == "c1"

    def test_article_id_required(self):
        with pytest.raises(ValueError, match="article_id is required"):
            CommentCreateRequest.from_body({"content": "Hello"})

    def test_content_required(self):
        with pytest.raises(ValueError, match="content is required"):
            CommentCreateRequest.from_body({"article_id": "art-1"})

    def test_content_too_long(self):
        with pytest.raises(ValueError, match="5000 characters"):
            CommentCreateRequest.from_body(
                {"article_id": "art-1", "content": "X" * 5001}
            )


class TestCommentUpdateRequest:
    def test_valid(self):
        req = CommentUpdateRequest.from_body({"content": "Updated content."})
        assert req.content == "Updated content."

    def test_content_required(self):
        with pytest.raises(ValueError, match="content is required"):
            CommentUpdateRequest.from_body({})

    def test_content_too_long(self):
        with pytest.raises(ValueError, match="5000 characters"):
            CommentUpdateRequest.from_body({"content": "X" * 5001})


class TestCommentModerateRequest:
    def test_hide_requires_reason(self):
        with pytest.raises(ValueError, match="reason required"):
            CommentModerateRequest.from_body({"is_hidden": True})

    def test_hide_with_reason_valid(self):
        req = CommentModerateRequest.from_body(
            {"is_hidden": True, "reason": "Spam content."}
        )
        assert req.is_hidden is True
        assert req.reason == "Spam content."

    def test_unhide_no_reason_required(self):
        req = CommentModerateRequest.from_body({"is_hidden": False})
        assert req.is_hidden is False

    def test_reason_too_long(self):
        with pytest.raises(ValueError, match="500 characters"):
            CommentModerateRequest.from_body({"is_hidden": True, "reason": "X" * 501})

    def test_is_hidden_must_be_bool(self):
        with pytest.raises(ValueError, match="boolean"):
            CommentModerateRequest.from_body({"is_hidden": "yes"})


# ─────────────────────────────────────────────────────────────────────────────
# Comments endpoint integration tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def svc():
    class _Env:
        pass

    return FakeCommentService(_Env())


@pytest.fixture
def client(svc):
    class _Env:
        pass

    return CommentsClient(_Env(), svc)


@pytest.fixture
def author_token():
    return _token(role="AUTHOR", sub="auth-user")


@pytest.fixture
def approver_token():
    return _token(role="APPROVER", sub="approver-user")


@pytest.fixture
def reader_token():
    return _token(role="READER", sub="reader-user")


class TestCommentsEndpoints:
    # ── List ──────────────────────────────────────────────────────────────────

    def test_list_requires_article_id(self, client):
        r = client.get("/api/comments")
        assert r.status_code == 422

    def test_list_for_article(self, client, svc):
        # Ensure at least one comment exists for art-1
        svc._comments["c1"].article_id = "art-1"
        r = client.get("/api/comments?article_id=art-1")
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert "pagination" in data

    # ── Create ────────────────────────────────────────────────────────────────

    def test_create_requires_auth(self, client):
        r = client.post(
            "/api/comments",
            json={"article_id": "art-1", "content": "Great article!"},
        )
        assert r.status_code == 401

    def test_create_comment(self, client, author_token, svc):
        r = client.post(
            "/api/comments",
            headers={"Authorization": f"Bearer {author_token}"},
            json={"article_id": "art-1", "content": "Great read!"},
        )
        assert r.status_code == 201
        assert r.json()["comment"]["article_id"] == "art-1"
        assert len(svc._created) == 1

    def test_create_validation_error(self, client, author_token):
        r = client.post(
            "/api/comments",
            headers={"Authorization": f"Bearer {author_token}"},
            json={"content": "Missing article_id"},
        )
        assert r.status_code == 422

    # ── Update ────────────────────────────────────────────────────────────────

    def test_update_requires_auth(self, client):
        r = client.put("/api/comments/c1", json={"content": "Edited."})
        assert r.status_code == 401

    def test_update_own_comment(self, client, author_token, svc):
        r = client.put(
            "/api/comments/c1",
            headers={"Authorization": f"Bearer {author_token}"},
            json={"content": "Updated comment content."},
        )
        assert r.status_code == 200
        assert svc._comments["c1"].content == "Updated comment content."

    def test_update_other_comment_forbidden(self, client, author_token):
        # c2 belongs to "other-user"
        r = client.put(
            "/api/comments/c2",
            headers={"Authorization": f"Bearer {author_token}"},
            json={"content": "Trying to edit someone else."},
        )
        assert r.status_code == 403

    # ── Delete ────────────────────────────────────────────────────────────────

    def test_delete_requires_auth(self, client):
        r = client.delete("/api/comments/c1")
        assert r.status_code == 401

    def test_admin_list_requires_auth(self, client):
        r = client.get("/api/comments/admin/all")
        assert r.status_code == 401

    def test_admin_list_requires_approver(self, client, reader_token):
        r = client.get(
            "/api/comments/admin/all",
            headers={"Authorization": f"Bearer {reader_token}"},
        )
        assert r.status_code == 403

    def test_admin_list_as_approver(self, client, approver_token, svc):
        r = client.get(
            "/api/comments/admin/all",
            headers={"Authorization": f"Bearer {approver_token}"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert "pagination" in data
