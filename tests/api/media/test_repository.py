import importlib

import pytest


media_repo_mod = importlib.import_module("api.media.repository")
MediaRepository = media_repo_mod.MediaRepository
Q = importlib.import_module("api.media.queries")


class _Bucket:
    def __init__(self):
        self.put_calls = []
        self.delete_calls = []

    async def get(self, key):
        return {"key": key}

    async def put(self, key, body, httpMetadata=None):
        self.put_calls.append((key, body, httpMetadata))

    async def delete(self, key):
        self.delete_calls.append(key)


@pytest.mark.asyncio
async def test_repository_requires_bucket():
    repo = MediaRepository(None)

    with pytest.raises(RuntimeError, match="not configured"):
        await repo.get("x")
    with pytest.raises(RuntimeError, match="not configured"):
        await repo.upload("u1", "image/png", b"x", 1)
    with pytest.raises(RuntimeError, match="not configured"):
        await repo.delete("x")


@pytest.mark.asyncio
async def test_upload_validation_and_success(monkeypatch):
    monkeypatch.setattr(media_repo_mod, "new_id", lambda: "fixed-id")

    bucket = _Bucket()
    repo = MediaRepository(bucket)

    with pytest.raises(ValueError, match="Unsupported type"):
        await repo.upload("u1", "text/plain", b"abc", 3)

    with pytest.raises(ValueError, match="File too large"):
        await repo.upload("u1", "image/png", b"a", Q.MAX_FILE_SIZE + 1)

    key = await repo.upload("u1", "image/jpeg", b"abc", 3)
    assert key == f"{Q.UPLOAD_PREFIX}/u1/fixed-id.jpg"
    assert bucket.put_calls[0][2]["contentType"] == "image/jpeg"


@pytest.mark.asyncio
async def test_get_and_delete_with_bucket():
    bucket = _Bucket()
    repo = MediaRepository(bucket)

    obj = await repo.get("uploads/u1/f.png")
    assert obj["key"] == "uploads/u1/f.png"

    await repo.delete("uploads/u1/f.png")
    assert bucket.delete_calls == ["uploads/u1/f.png"]
