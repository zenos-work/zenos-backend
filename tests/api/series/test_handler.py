import importlib

import pytest


series_handler = importlib.import_module("api.series.handler")


class _Req:
    def __init__(self, method, path, body=None):
        self.method = method
        self.url = f"https://test.local{path}"
        self.headers = {}
        self._body = body or {}

    async def json(self):
        return self._body


class _Obj:
    def __init__(self, id):
        self.id = id

    def to_dict(self):
        return {"id": self.id, "name": f"name-{self.id}"}


class _ListResult:
    def to_dict(self):
        return {"items": [{"id": "s1"}], "total": 1}


class _Svc:
    async def create(self, user_id, req):
        if req.name == "explode":
            raise RuntimeError("x")
        return _Obj("s1")

    async def list_by_author(self, user_id, page, limit):
        if page == 99:
            raise RuntimeError("x")
        return _ListResult()

    async def get_by_id(self, series_id):
        if series_id == "missing":
            return None
        if series_id == "boom":
            raise RuntimeError("x")
        return _Obj(series_id)

    async def list_series_articles(self, series_id):
        if series_id == "err":
            raise RuntimeError("x")
        return [_Obj("a1"), _Obj("a2")]

    async def update(self, series_id, user_id, req):
        if req.name == "invalid":
            raise ValueError("invalid")
        if series_id == "missing":
            return None
        if series_id == "boom":
            raise RuntimeError("x")
        return _Obj(series_id)

    async def delete(self, series_id, user_id):
        if series_id == "boom":
            raise RuntimeError("x")
        return series_id != "missing"

    async def assign_article(self, article_id, series_id, user_id, req):
        if req.part_number == -1:
            raise ValueError("invalid")
        if article_id == "boom":
            raise RuntimeError("x")
        return article_id != "missing"

    async def remove_article(self, article_id, series_id, user_id):
        if article_id == "boom":
            raise RuntimeError("x")
        return article_id != "missing"


class _Env:
    pass


@pytest.fixture
def svc(monkeypatch):
    s = _Svc()
    monkeypatch.setattr(series_handler, "SeriesService", lambda env, ctx: s)
    return s


async def _auth(_req, _env):
    return {"sub": "u1"}


async def _no_auth(_req, _env):
    return None


class TestSeriesHandler:
    @pytest.mark.asyncio
    async def test_unauthorized(self, monkeypatch, svc):
        monkeypatch.setattr(series_handler, "get_user", _no_auth)
        r = await series_handler.handle_series(
            _Req("GET", "/api/series"), _Env(), "/api/series", "GET", {}, object()
        )
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_create_paths(self, monkeypatch, svc):
        monkeypatch.setattr(series_handler, "get_user", _auth)

        ok = await series_handler.handle_series(
            _Req("POST", "/api/series", {"name": "Alpha"}),
            _Env(),
            "/api/series",
            "POST",
            {},
            object(),
        )
        assert ok.status_code == 200

        bad_req = await series_handler.handle_series(
            _Req("POST", "/api/series", {"name": ""}),
            _Env(),
            "/api/series",
            "POST",
            {},
            object(),
        )
        assert bad_req.status_code == 400

        err = await series_handler.handle_series(
            _Req("POST", "/api/series", {"name": "explode"}),
            _Env(),
            "/api/series",
            "POST",
            {},
            object(),
        )
        assert err.status_code == 500

    @pytest.mark.asyncio
    async def test_list_and_get_paths(self, monkeypatch, svc):
        monkeypatch.setattr(series_handler, "get_user", _auth)

        list_ok = await series_handler.handle_series(
            _Req("GET", "/api/series?page=1&limit=20"),
            _Env(),
            "/api/series",
            "GET",
            {"page": ["1"], "limit": ["20"]},
            object(),
        )
        assert list_ok.status_code == 200

        list_err = await series_handler.handle_series(
            _Req("GET", "/api/series?page=99&limit=20"),
            _Env(),
            "/api/series",
            "GET",
            {"page": ["99"], "limit": ["20"]},
            object(),
        )
        assert list_err.status_code == 500

        get_ok = await series_handler.handle_series(
            _Req("GET", "/api/series/s1"),
            _Env(),
            "/api/series/s1",
            "GET",
            {},
            object(),
        )
        assert get_ok.status_code == 200

        get_missing = await series_handler.handle_series(
            _Req("GET", "/api/series/missing"),
            _Env(),
            "/api/series/missing",
            "GET",
            {},
            object(),
        )
        assert get_missing.status_code == 404

        get_err = await series_handler.handle_series(
            _Req("GET", "/api/series/boom"),
            _Env(),
            "/api/series/boom",
            "GET",
            {},
            object(),
        )
        assert get_err.status_code == 500

    @pytest.mark.asyncio
    async def test_articles_update_delete_paths(self, monkeypatch, svc):
        monkeypatch.setattr(series_handler, "get_user", _auth)

        articles_ok = await series_handler.handle_series(
            _Req("GET", "/api/series/s1/articles"),
            _Env(),
            "/api/series/s1/articles",
            "GET",
            {},
            object(),
        )
        assert articles_ok.status_code == 200

        articles_missing = await series_handler.handle_series(
            _Req("GET", "/api/series/missing/articles"),
            _Env(),
            "/api/series/missing/articles",
            "GET",
            {},
            object(),
        )
        assert articles_missing.status_code == 404

        articles_err = await series_handler.handle_series(
            _Req("GET", "/api/series/err/articles"),
            _Env(),
            "/api/series/err/articles",
            "GET",
            {},
            object(),
        )
        assert articles_err.status_code == 500

        upd_ok = await series_handler.handle_series(
            _Req("PUT", "/api/series/s1", {"name": "Beta"}),
            _Env(),
            "/api/series/s1",
            "PUT",
            {},
            object(),
        )
        assert upd_ok.status_code == 200

        upd_missing = await series_handler.handle_series(
            _Req("PUT", "/api/series/missing", {"name": "Beta"}),
            _Env(),
            "/api/series/missing",
            "PUT",
            {},
            object(),
        )
        assert upd_missing.status_code == 404

        upd_value = await series_handler.handle_series(
            _Req("PUT", "/api/series/s1", {"name": "invalid"}),
            _Env(),
            "/api/series/s1",
            "PUT",
            {},
            object(),
        )
        assert upd_value.status_code == 400

        upd_err = await series_handler.handle_series(
            _Req("PUT", "/api/series/boom", {"name": "Beta"}),
            _Env(),
            "/api/series/boom",
            "PUT",
            {},
            object(),
        )
        assert upd_err.status_code == 500

        del_ok = await series_handler.handle_series(
            _Req("DELETE", "/api/series/s1"),
            _Env(),
            "/api/series/s1",
            "DELETE",
            {},
            object(),
        )
        assert del_ok.status_code == 200

        del_missing = await series_handler.handle_series(
            _Req("DELETE", "/api/series/missing"),
            _Env(),
            "/api/series/missing",
            "DELETE",
            {},
            object(),
        )
        assert del_missing.status_code == 404

        del_err = await series_handler.handle_series(
            _Req("DELETE", "/api/series/boom"),
            _Env(),
            "/api/series/boom",
            "DELETE",
            {},
            object(),
        )
        assert del_err.status_code == 500

    @pytest.mark.asyncio
    async def test_assign_remove_and_not_found(self, monkeypatch, svc):
        monkeypatch.setattr(series_handler, "get_user", _auth)

        assign_missing_id = await series_handler.handle_series(
            _Req(
                "POST", "/api/series/s1/articles", {"series_id": "s1", "part_number": 1}
            ),
            _Env(),
            "/api/series/s1/articles",
            "POST",
            {},
            object(),
        )
        assert assign_missing_id.status_code == 400

        assign_ok = await series_handler.handle_series(
            _Req(
                "POST",
                "/api/series/s1/articles/a1",
                {"series_id": "s1", "part_number": 1},
            ),
            _Env(),
            "/api/series/s1/articles/a1",
            "POST",
            {},
            object(),
        )
        assert assign_ok.status_code == 200

        assign_missing = await series_handler.handle_series(
            _Req(
                "POST",
                "/api/series/s1/articles/missing",
                {"series_id": "s1", "part_number": 1},
            ),
            _Env(),
            "/api/series/s1/articles/missing",
            "POST",
            {},
            object(),
        )
        assert assign_missing.status_code == 404

        assign_value = await series_handler.handle_series(
            _Req(
                "POST",
                "/api/series/s1/articles/a1",
                {"series_id": "s1", "part_number": -1},
            ),
            _Env(),
            "/api/series/s1/articles/a1",
            "POST",
            {},
            object(),
        )
        assert assign_value.status_code == 400

        assign_err = await series_handler.handle_series(
            _Req(
                "POST",
                "/api/series/s1/articles/boom",
                {"series_id": "s1", "part_number": 1},
            ),
            _Env(),
            "/api/series/s1/articles/boom",
            "POST",
            {},
            object(),
        )
        assert assign_err.status_code == 500

        remove_missing_id = await series_handler.handle_series(
            _Req("DELETE", "/api/series/s1/articles"),
            _Env(),
            "/api/series/s1/articles",
            "DELETE",
            {},
            object(),
        )
        assert remove_missing_id.status_code == 400

        remove_ok = await series_handler.handle_series(
            _Req("DELETE", "/api/series/s1/articles/a1"),
            _Env(),
            "/api/series/s1/articles/a1",
            "DELETE",
            {},
            object(),
        )
        assert remove_ok.status_code == 200

        remove_missing = await series_handler.handle_series(
            _Req("DELETE", "/api/series/s1/articles/missing"),
            _Env(),
            "/api/series/s1/articles/missing",
            "DELETE",
            {},
            object(),
        )
        assert remove_missing.status_code == 404

        remove_err = await series_handler.handle_series(
            _Req("DELETE", "/api/series/s1/articles/boom"),
            _Env(),
            "/api/series/s1/articles/boom",
            "DELETE",
            {},
            object(),
        )
        assert remove_err.status_code == 500

        fallback = await series_handler.handle_series(
            _Req("GET", "/api/series/s1/other"),
            _Env(),
            "/api/series/s1/other",
            "GET",
            {},
            object(),
        )
        assert fallback.status_code == 404
