from api.media.repository import MediaRepository
from api.media.queries import UPLOAD_PREFIX


class MediaService:
    """Business logic for media uploads. Zero SQL."""

    def __init__(self, env, ctx=None):
        self._repo = MediaRepository(env.MEDIA, ctx)
        self._base_url = getattr(env, "MEDIA_URL", "https://media.zenos.work")
        self._ctx = ctx

    async def _log(self, name: str, data: dict = None) -> None:
        if self._ctx:
            await self._ctx.log.event(name, data=data)

    async def upload(self, user_id: str, request) -> dict:
        content_type = request.headers.get("Content-Type", "")
        body = await request.arrayBuffer()
        size = body.byteLength

        try:
            key = await self._repo.upload(user_id, content_type, body, size)
        except ValueError:
            raise

        url = f"{self._base_url}/{key}"
        await self._log(
            "media.uploaded",
            {
                "user_id": user_id,
                "key": key,
                "size_bytes": size,
                "content_type": content_type,
            },
        )
        return {"url": url, "key": key}

    async def delete(self, user_id: str, key: str, is_superadmin: bool = False) -> None:
        if not key.startswith(f"{UPLOAD_PREFIX}/{user_id}/") and not is_superadmin:
            raise PermissionError("Forbidden")
        await self._repo.delete(key)
