"""
Phase 9 – Article tests.

Covers:
  - ArticleCreateRequest validation
  - ArticleUpdateRequest validation
  - Article.to_dict() scope filtering
  - ArticleService.transition() state machine
  - All articles endpoint routes (CRUD + full workflow)
"""

import asyncio
import importlib
from urllib.parse import parse_qs, urlparse

import pytest

ArticleCreateRequest = importlib.import_module(
    "models.article.requests"
).ArticleCreateRequest
ArticleUpdateRequest = importlib.import_module(
    "models.article.requests"
).ArticleUpdateRequest
RejectArticleRequest = importlib.import_module(
    "models.article.requests"
).RejectArticleRequest
Article = importlib.import_module("models.article.model").Article
ArticleStatus = importlib.import_module("models.common.enums").ArticleStatus
Scope = importlib.import_module("models.common.enums").Scope
Tag = importlib.import_module("models.tag.model").Tag
create_token = importlib.import_module("auth.jwt_handler").create_token
articles_handler = importlib.import_module("api.articles.handler")

_JWT_SECRET = "test-secret"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers / fixtures
# ─────────────────────────────────────────────────────────────────────────────


def _make_article(
    id="art-1",
    status=ArticleStatus.DRAFT,
    author_id="auth-user",
    title="My Test Article",
):
    return Article(
        id=id,
        title=title,
        slug="my-test-article",
        status=status,
        author_id=author_id,
        views_count=0,
        likes_count=0,
        comments_count=0,
        is_featured=0,
        read_time_minutes=3,
        created_at="2026-03-18T10:00:00Z",
        content="This is the full article body content for testing purposes.",
        updated_at="2026-03-18T10:00:00Z",
    )


class FakeRequest:
    def __init__(self, method, url, headers=None, json_body=None):
        self.method = method
        self.url = f"https://testserver{url}"
        self.headers = headers or {}
        self._json_body = json_body

    async def json(self):
        return self._json_body if self._json_body is not None else {}


class FakeEnv:
    JWT_SECRET = _JWT_SECRET


class FakeCtx:
    trace_id = "test-trace-id"

    class log:
        @staticmethod
        async def event(name, data=None):
            pass


class FakeArticleService:
    """In-memory service that mirrors ArticleService's interface."""

    def __init__(self, env, ctx=None):
        self._articles = {
            "art-draft": _make_article(
                id="art-draft", status=ArticleStatus.DRAFT, author_id="auth-user"
            ),
            "art-submitted": _make_article(
                id="art-submitted",
                status=ArticleStatus.SUBMITTED,
                author_id="auth-user",
            ),
            "art-approved": _make_article(
                id="art-approved",
                status=ArticleStatus.APPROVED,
                author_id="auth-user",
            ),
            "art-published": _make_article(
                id="art-published",
                status=ArticleStatus.PUBLISHED,
                author_id="auth-user",
            ),
            "art-rejected": _make_article(
                id="art-rejected",
                status=ArticleStatus.REJECTED,
                author_id="auth-user",
            ),
            "art-other": _make_article(
                id="art-other", status=ArticleStatus.DRAFT, author_id="other-user"
            ),
        }
        self._deleted = []
        self._transitions = []

    async def list_published(self, page, limit, tag=None, search=None):
        from models.common.pagination import PaginatedResponse

        articles = [
            a for a in self._articles.values() if a.status == ArticleStatus.PUBLISHED
        ]
        return PaginatedResponse.of(articles, page, limit)

    async def list_by_author(self, author_id, page, limit, status=None):
        from models.common.pagination import PaginatedResponse

        articles = [
            a
            for a in self._articles.values()
            if a.author_id == author_id and (status is None or a.status == status)
        ]
        return PaginatedResponse.of(articles, page, limit)

    async def get_by_id_or_slug(self, identifier):
        return self._articles.get(identifier)

    async def get_owner(self, article_id):
        a = self._articles.get(article_id)
        return a.author_id if a else None

    async def create(self, req, author_id):
        a = _make_article(
            id="art-new",
            status=ArticleStatus.DRAFT,
            author_id=author_id,
            title=req.title,
        )
        a.content = req.content
        self._articles["art-new"] = a
        return a

    async def update(self, article_id, req, current):
        a = self._articles[article_id]
        if req.title:
            a.title = req.title
        if req.content:
            a.content = req.content
        return a

    async def delete(self, article_id):
        self._deleted.append(article_id)
        self._articles.pop(article_id, None)

    async def transition(self, article_id, new_status, actor_id=None, note=None):
        self._transitions.append(
            {
                "article_id": article_id,
                "new_status": new_status,
                "actor_id": actor_id,
                "note": note,
            }
        )
        a = self._articles.get(article_id)
        if a:
            a.status = new_status
        return new_status

    async def increment_views(self, article_id):
        pass


class ArticlesClient:
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

        import api.articles.handler as _h

        original = _h.ArticleService
        _h.ArticleService = _make_svc
        try:
            result = asyncio.run(
                articles_handler.handle_articles(
                    request,
                    _Env(),
                    parsed.path,
                    method,
                    parse_qs(parsed.query),
                    FakeCtx(),
                )
            )
        finally:
            _h.ArticleService = original
        return result


def _token(role="AUTHOR", sub="auth-user"):
    return create_token({"sub": sub, "role": role}, _JWT_SECRET)


# ─────────────────────────────────────────────────────────────────────────────
# Model Validation Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestArticleCreateRequest:
    def test_valid_minimal(self):
        req = ArticleCreateRequest.from_body(
            {
                "title": "My Title Here",
                "content": "A" * 60,
            }
        )
        assert req.title == "My Title Here"
        assert req.subtitle is None
        assert req.tag_ids == []

    def test_valid_with_all_fields(self):
        req = ArticleCreateRequest.from_body(
            {
                "title": "Full Article",
                "content": "B" * 100,
                "subtitle": "A short sub",
                "content_type": "case-study",
                "cover_image_url": "https://example.com/img.jpg",
                "tag_ids": ["t1", "t2"],
            }
        )
        assert req.subtitle == "A short sub"
        assert req.content_type == "case-study"
        assert len(req.tag_ids) == 2

    def test_title_required(self):
        with pytest.raises(ValueError, match="Title is required"):
            ArticleCreateRequest.from_body({"content": "A" * 60})

    def test_title_too_short(self):
        with pytest.raises(ValueError, match="at least 5 characters"):
            ArticleCreateRequest.from_body({"title": "Hi", "content": "A" * 60})

    def test_title_too_long(self):
        with pytest.raises(ValueError, match="200 characters"):
            ArticleCreateRequest.from_body({"title": "X" * 201, "content": "A" * 60})

    def test_content_required(self):
        with pytest.raises(ValueError, match="Content is required"):
            ArticleCreateRequest.from_body({"title": "Good Title"})

    def test_content_too_short(self):
        with pytest.raises(ValueError, match="at least 50 characters"):
            ArticleCreateRequest.from_body(
                {"title": "Good Title", "content": "Too short"}
            )

    def test_content_too_long(self):
        with pytest.raises(ValueError, match="50,000 characters"):
            ArticleCreateRequest.from_body(
                {"title": "Good Title", "content": "A" * 50001}
            )

    def test_subtitle_too_long(self):
        with pytest.raises(ValueError, match="500 characters"):
            ArticleCreateRequest.from_body(
                {
                    "title": "Good Title",
                    "content": "A" * 60,
                    "subtitle": "X" * 501,
                }
            )

    def test_too_many_tags(self):
        with pytest.raises(ValueError, match="10 tags"):
            ArticleCreateRequest.from_body(
                {
                    "title": "Good Title",
                    "content": "A" * 60,
                    "tag_ids": [f"t{i}" for i in range(11)],
                }
            )

    def test_tag_ids_must_be_list(self):
        with pytest.raises(ValueError, match="must be a list"):
            ArticleCreateRequest.from_body(
                {
                    "title": "Good Title",
                    "content": "A" * 60,
                    "tag_ids": "not-a-list",
                }
            )

    def test_content_type_must_be_slug_like(self):
        with pytest.raises(
            ValueError,
            match="content_type must be lowercase letters/numbers with optional hyphens",
        ):
            ArticleCreateRequest.from_body(
                {
                    "title": "Good Title",
                    "content": "A" * 60,
                    "content_type": "Memo Type",
                }
            )


class TestArticleUpdateRequest:
    def test_all_fields_optional(self):
        req = ArticleUpdateRequest.from_body({})
        assert req.title is None
        assert req.content is None

    def test_title_too_short_when_provided(self):
        with pytest.raises(ValueError, match="at least 5 characters"):
            ArticleUpdateRequest.from_body({"title": "Hi"})

    def test_content_too_short_when_provided(self):
        with pytest.raises(ValueError, match="at least 50 characters"):
            ArticleUpdateRequest.from_body({"content": "Short"})

    def test_valid_partial_update(self):
        req = ArticleUpdateRequest.from_body({"title": "New Good Title"})
        assert req.title == "New Good Title"
        assert req.content is None

    def test_invalid_content_type_when_provided(self):
        with pytest.raises(
            ValueError,
            match="content_type must be lowercase letters/numbers with optional hyphens",
        ):
            ArticleUpdateRequest.from_body({"content_type": "Memo Type"})


class TestRejectArticleRequest:
    def test_valid(self):
        req = RejectArticleRequest.from_body({"note": "Needs major revisions."})
        assert req.note == "Needs major revisions."

    def test_note_required(self):
        with pytest.raises(ValueError, match="required"):
            RejectArticleRequest.from_body({})

    def test_note_too_short(self):
        with pytest.raises(ValueError, match="10 characters"):
            RejectArticleRequest.from_body({"note": "Short"})

    def test_note_too_long(self):
        with pytest.raises(ValueError, match="1000 characters"):
            RejectArticleRequest.from_body({"note": "X" * 1001})


# ─────────────────────────────────────────────────────────────────────────────
# Article Model Serialisation Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestArticleModel:
    def test_list_scope_excludes_content(self):
        a = _make_article()
        d = a.to_dict(Scope.LIST)
        assert "content" not in d
        assert "title" in d

    def test_detail_scope_includes_content(self):
        a = _make_article()
        a.content = "Full article content for reading."
        d = a.to_dict(Scope.DETAIL)
        assert "content" in d

    def test_null_fields_excluded(self):
        a = _make_article()
        a.subtitle = None
        d = a.to_dict(Scope.LIST)
        assert "subtitle" not in d

    def test_tags_serialised_as_dicts(self):
        a = _make_article()
        a.tags = [Tag(id="t1", name="Python", slug="python", article_count=5)]
        d = a.to_dict(Scope.LIST)
        assert d["tags"] == [
            {"id": "t1", "name": "Python", "slug": "python", "article_count": 5}
        ]

    def test_admin_scope_includes_rejection_note(self):
        a = _make_article(status=ArticleStatus.REJECTED)
        a.rejection_note = "Needs more sources."
        d = a.to_dict(Scope.ADMIN)
        assert d["rejection_note"] == "Needs more sources."


# ─────────────────────────────────────────────────────────────────────────────
# ArticleService transition() unit tests (pure state machine)
# ─────────────────────────────────────────────────────────────────────────────


class TestArticleServiceTransition:
    """Test the service-level state machine without real DB (stub repo)."""

    def _make_service(self):
        ArticleService = importlib.import_module("api.articles.service").ArticleService

        class _StubRepo:
            def __init__(self):
                self.calls = []

            async def set_status(self, article_id, status, **kwargs):
                self.calls.append((article_id, status, kwargs))

        class _StubEnv:
            class DB:
                pass

        svc = ArticleService.__new__(ArticleService)
        repo = _StubRepo()
        svc._repo = repo
        svc._ctx = None
        return svc, repo

    def test_transition_submit(self):
        svc, repo = self._make_service()
        result = asyncio.run(svc.transition("a1", ArticleStatus.SUBMITTED))
        assert result == ArticleStatus.SUBMITTED
        assert repo.calls[0][1] == ArticleStatus.SUBMITTED

    def test_transition_approve(self):
        svc, repo = self._make_service()
        asyncio.run(svc.transition("a1", ArticleStatus.APPROVED, actor_id="u1"))
        assert repo.calls[0][2]["approved_by"] == "u1"

    def test_transition_reject(self):
        svc, repo = self._make_service()
        asyncio.run(
            svc.transition("a1", ArticleStatus.REJECTED, note="Needs revision.")
        )
        assert repo.calls[0][2]["rejection_note"] == "Needs revision."

    def test_transition_publish(self):
        svc, repo = self._make_service()
        asyncio.run(svc.transition("a1", ArticleStatus.PUBLISHED))
        assert repo.calls[0][2].get("publish") is True

    def test_transition_archive(self):
        svc, repo = self._make_service()
        result = asyncio.run(svc.transition("a1", ArticleStatus.ARCHIVED))
        assert result == ArticleStatus.ARCHIVED

    def test_transition_unknown_raises(self):
        svc, _ = self._make_service()
        with pytest.raises(ValueError, match="Unknown status"):
            asyncio.run(svc.transition("a1", "BLORP"))


# ─────────────────────────────────────────────────────────────────────────────
# Articles endpoint integration tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def svc():
    return FakeArticleService(FakeEnv())


@pytest.fixture
def client(svc):
    return ArticlesClient(FakeEnv(), svc)


@pytest.fixture
def author_token():
    return _token(role="AUTHOR", sub="auth-user")


@pytest.fixture
def approver_token():
    return _token(role="APPROVER", sub="approver-user")


@pytest.fixture
def reader_token():
    return _token(role="READER", sub="reader-user")


class TestArticlesEndpoints:
    # ── List/Get ──────────────────────────────────────────────────────────────

    def test_list_published(self, client):
        r = client.get("/api/articles")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "page" in data
        assert "limit" in data
        assert "total" in data

    def test_get_article_by_id(self, client):
        r = client.get("/api/articles/art-published")
        assert r.status_code == 200
        assert r.json()["article"]["id"] == "art-published"

    def test_get_article_not_found(self, client):
        r = client.get("/api/articles/missing")
        assert r.status_code == 404

    # ── Create ────────────────────────────────────────────────────────────────

    def test_create_requires_auth(self, client):
        r = client.post("/api/articles", json={"title": "x" * 10, "content": "c" * 60})
        assert r.status_code == 401

    def test_create_reader_is_forbidden(self, client, reader_token):
        r = client.post(
            "/api/articles",
            headers={"Authorization": f"Bearer {reader_token}"},
            json={"title": "x" * 10, "content": "c" * 60},
        )
        assert r.status_code == 403

    def test_create_author_succeeds(self, client, author_token, svc):
        r = client.post(
            "/api/articles",
            headers={"Authorization": f"Bearer {author_token}"},
            json={"title": "A Brand New Article", "content": "B" * 80},
        )
        assert r.status_code == 201
        assert r.json()["article"]["author_id"] == "auth-user"

    def test_create_validation_error(self, client, author_token):
        r = client.post(
            "/api/articles",
            headers={"Authorization": f"Bearer {author_token}"},
            json={"title": "Hi"},  # content missing
        )
        assert r.status_code == 422

    # ── Update ────────────────────────────────────────────────────────────────

    def test_update_requires_auth(self, client):
        r = client.put("/api/articles/art-draft", json={"title": "New Title Here"})
        assert r.status_code == 401

    def test_update_non_owner_forbidden(self, client, author_token):
        # art-other belongs to "other-user", not "auth-user"
        r = client.put(
            "/api/articles/art-other",
            headers={"Authorization": f"Bearer {author_token}"},
            json={"title": "New Title Here"},
        )
        assert r.status_code == 403

    def test_update_non_editable_conflict(self, client, author_token):
        # art-submitted is SUBMITTED, not editable
        r = client.put(
            "/api/articles/art-submitted",
            headers={"Authorization": f"Bearer {author_token}"},
            json={"title": "New Title Here"},
        )
        assert r.status_code == 409

    def test_update_draft_as_owner(self, client, author_token, svc):
        r = client.put(
            "/api/articles/art-draft",
            headers={"Authorization": f"Bearer {author_token}"},
            json={"title": "Updated Title Here"},
        )
        assert r.status_code == 200
        assert svc._articles["art-draft"].title == "Updated Title Here"

    # ── Delete ────────────────────────────────────────────────────────────────

    def test_delete_not_owner_forbidden(self, client, author_token):
        r = client.delete(
            "/api/articles/art-other",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 403

    def test_delete_as_owner(self, client, author_token, svc):
        r = client.delete(
            "/api/articles/art-draft",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 200
        assert r.json()["deleted"] is True
        assert "art-draft" in svc._deleted

    # ── Workflow: Submit ──────────────────────────────────────────────────────

    def test_submit_requires_auth(self, client):
        r = client.post("/api/articles/art-draft/submit")
        assert r.status_code == 401

    def test_submit_draft(self, client, author_token, svc):
        r = client.post(
            "/api/articles/art-draft/submit",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == ArticleStatus.SUBMITTED

    def test_submit_for_approval_alias(self, client, author_token, svc):
        r = client.post(
            "/api/articles/art-rejected/submit-for-approval",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == ArticleStatus.SUBMITTED

    def test_submit_non_editable_conflict(self, client, author_token):
        r = client.post(
            "/api/articles/art-submitted/submit",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 409

    def test_submit_not_owner_forbidden(self, client, approver_token):
        # approver-user is not the owner of art-draft
        r = client.post(
            "/api/articles/art-draft/submit",
            headers={"Authorization": f"Bearer {approver_token}"},
        )
        assert r.status_code == 403

    # ── Workflow: Approve ─────────────────────────────────────────────────────

    def test_approve_requires_approver_role(self, client, author_token):
        r = client.post(
            "/api/articles/art-submitted/approve",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 403

    def test_approve_non_submitted_conflict(self, client, approver_token):
        r = client.post(
            "/api/articles/art-draft/approve",
            headers={"Authorization": f"Bearer {approver_token}"},
        )
        assert r.status_code == 409

    def test_approve_submitted(self, client, approver_token, svc):
        r = client.post(
            "/api/articles/art-submitted/approve",
            headers={"Authorization": f"Bearer {approver_token}"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == ArticleStatus.APPROVED

    # ── Workflow: Reject ──────────────────────────────────────────────────────

    def test_reject_non_submitted_conflict(self, client, approver_token):
        r = client.post(
            "/api/articles/art-draft/reject",
            headers={"Authorization": f"Bearer {approver_token}"},
            json={"note": "Needs much more detail."},
        )
        assert r.status_code == 409

    def test_reject_requires_note(self, client, approver_token):
        r = client.post(
            "/api/articles/art-submitted/reject",
            headers={"Authorization": f"Bearer {approver_token}"},
            json={},
        )
        assert r.status_code == 422

    def test_reject_submitted(self, client, approver_token, svc):
        r = client.post(
            "/api/articles/art-submitted/reject",
            headers={"Authorization": f"Bearer {approver_token}"},
            json={"note": "Needs much more detail and citations."},
        )
        assert r.status_code == 200
        assert r.json()["status"] == ArticleStatus.REJECTED
        assert svc._transitions[-1]["note"] == "Needs much more detail and citations."

    # ── Workflow: Publish ─────────────────────────────────────────────────────

    def test_publish_requires_approver_role(self, client, author_token):
        r = client.post(
            "/api/articles/art-approved/publish",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 403

    def test_publish_non_approved_conflict(self, client, approver_token):
        r = client.post(
            "/api/articles/art-submitted/publish",
            headers={"Authorization": f"Bearer {approver_token}"},
        )
        assert r.status_code == 409

    def test_publish_approved(self, client, approver_token):
        r = client.post(
            "/api/articles/art-approved/publish",
            headers={"Authorization": f"Bearer {approver_token}"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == ArticleStatus.PUBLISHED

    # ── Workflow: Archive ─────────────────────────────────────────────────────

    def test_archive_as_owner(self, client, author_token):
        r = client.post(
            "/api/articles/art-published/archive",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == ArticleStatus.ARCHIVED

    def test_archive_already_archived_conflict(self, client, author_token, svc):
        # Force the article to ARCHIVED first
        svc._articles["art-published"].status = ArticleStatus.ARCHIVED
        r = client.post(
            "/api/articles/art-published/archive",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 409

    def test_archive_requires_auth(self, client):
        r = client.post("/api/articles/art-draft/archive")
        assert r.status_code == 401

    # ── Mine ─────────────────────────────────────────────────────────────────

    def test_list_mine_requires_auth(self, client):
        r = client.get("/api/articles/mine")
        assert r.status_code == 401

    def test_list_mine_returns_own_articles(self, client, author_token):
        r = client.get(
            "/api/articles/mine",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
