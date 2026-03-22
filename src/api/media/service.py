from api.media.repository import MediaRepository
from api.media.queries import UPLOAD_PREFIX
from urllib.parse import urlsplit


class MediaService:
    """Business logic for media uploads. Zero SQL."""

    def __init__(self, env, ctx=None):
        media_bucket = getattr(env, "MEDIA", None)
        self._repo = MediaRepository(media_bucket, ctx)
        # When MEDIA_URL is not configured, use API route so local dev still works.
        self._base_url = getattr(env, "MEDIA_URL", "/api/media")
        self._ctx = ctx

    async def _log(self, name: str, data: dict = None) -> None:
        if self._ctx:
            await self._ctx.log.event(name, data=data)

    def _detect_image_content_type(self, body: bytes) -> str | None:
        if body.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if body.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if body.startswith((b"GIF87a", b"GIF89a")):
            return "image/gif"
        if len(body) >= 12 and body[:4] == b"RIFF" and body[8:12] == b"WEBP":
            return "image/webp"
        return None

    async def upload(self, user_id: str, request) -> dict:
        raw_content_type = request.headers.get("Content-Type", "")
        content_type = raw_content_type.split(";", 1)[0].strip().lower()
        # Python Workers runtime exposes request.bytes() for binary bodies;
        # arrayBuffer() is the JS-only Fetch API and is not available here.
        body = await request.bytes()
        size = len(body)
        if size <= 0:
            raise ValueError("Empty file upload")

        # Be tolerant to browser/vendor aliases and unknown binary headers.
        if content_type == "image/jpg":
            content_type = "image/jpeg"
        if content_type in ("", "application/octet-stream"):
            detected_type = self._detect_image_content_type(body)
            if detected_type:
                content_type = detected_type

        try:
            key = await self._repo.upload(user_id, content_type, body, size)
        except ValueError:
            raise

        base_url = self._base_url
        if isinstance(base_url, str) and base_url.startswith("/"):
            request_url = str(getattr(request, "url", "") or "")
            parts = urlsplit(request_url)
            if parts.scheme and parts.netloc:
                base_url = f"{parts.scheme}://{parts.netloc}{base_url}"

        url = f"{base_url}/{key}"
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

    async def get_public(self, key: str):
        obj = await self._repo.get(key)
        if not obj:
            return None
        return obj

    async def delete(self, user_id: str, key: str, is_superadmin: bool = False) -> None:
        if not key.startswith(f"{UPLOAD_PREFIX}/{user_id}/") and not is_superadmin:
            raise PermissionError("Forbidden")
        await self._repo.delete(key)
