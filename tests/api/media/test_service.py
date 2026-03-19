import pytest

from api.media.service import MediaService


class _Req:
    def __init__(
        self, body=b"abc", content_type="image/png", url="https://api.local/upload"
    ):
        self._body = body
        self.headers = {"Content-Type": content_type}
        self.url = url

    async def bytes(self):
        return self._body


class _Repo:
    def __init__(self):
        self.upload_calls = []
        self.deleted = []
        self.get_result = None

    async def upload(self, user_id, content_type, body, size):
        self.upload_calls.append((user_id, content_type, body, size))
        return "uploads/u1/file.png"

    async def get(self, key):
        return self.get_result

    async def delete(self, key):
        self.deleted.append(key)


class _Log:
    def __init__(self):
        self.events = []

    async def event(self, name, data=None):
        self.events.append((name, data))


class _Ctx:
    def __init__(self):
        self.log = _Log()


class _Env:
    MEDIA_URL = "/api/media"


class TestMediaService:
    @pytest.mark.asyncio
    async def test_upload_builds_absolute_url_for_relative_media_base(
        self, monkeypatch
    ):
        svc = MediaService(_Env(), _Ctx())
        repo = _Repo()
        monkeypatch.setattr(svc, "_repo", repo)

        result = await svc.upload(
            "u1", _Req(body=b"abc", content_type="image/png; charset=utf-8")
        )

        assert repo.upload_calls[0][0] == "u1"
        assert repo.upload_calls[0][1] == "image/png"
        assert repo.upload_calls[0][3] == 3
        assert result["url"] == "https://api.local/api/media/uploads/u1/file.png"
        assert result["key"] == "uploads/u1/file.png"

    @pytest.mark.asyncio
    async def test_upload_raises_for_empty_body(self, monkeypatch):
        svc = MediaService(_Env(), _Ctx())
        repo = _Repo()
        monkeypatch.setattr(svc, "_repo", repo)

        with pytest.raises(ValueError, match="Empty file upload"):
            await svc.upload("u1", _Req(body=b""))

    @pytest.mark.asyncio
    async def test_upload_propagates_repository_validation_error(self, monkeypatch):
        svc = MediaService(_Env(), _Ctx())

        class _BadRepo(_Repo):
            async def upload(self, user_id, content_type, body, size):
                raise ValueError("unsupported content type")

        monkeypatch.setattr(svc, "_repo", _BadRepo())

        with pytest.raises(ValueError, match="unsupported content type"):
            await svc.upload("u1", _Req(body=b"x", content_type="text/plain"))

    @pytest.mark.asyncio
    async def test_get_public_returns_none_or_object(self, monkeypatch):
        svc = MediaService(_Env(), _Ctx())
        repo = _Repo()
        monkeypatch.setattr(svc, "_repo", repo)

        repo.get_result = None
        assert await svc.get_public("uploads/u1/file.png") is None

        repo.get_result = {"key": "uploads/u1/file.png"}
        assert await svc.get_public("uploads/u1/file.png") == {
            "key": "uploads/u1/file.png"
        }

    @pytest.mark.asyncio
    async def test_delete_enforces_user_scope_unless_superadmin(self, monkeypatch):
        svc = MediaService(_Env(), _Ctx())
        repo = _Repo()
        monkeypatch.setattr(svc, "_repo", repo)

        with pytest.raises(PermissionError, match="Forbidden"):
            await svc.delete("u1", "uploads/other/file.png", is_superadmin=False)

        await svc.delete("u1", "uploads/u1/file.png", is_superadmin=False)
        await svc.delete("u1", "uploads/other/file.png", is_superadmin=True)

        assert repo.deleted == ["uploads/u1/file.png", "uploads/other/file.png"]
