from pyodide.ffi import to_js

from api.media.queries import ALLOWED_TYPES, MAX_FILE_SIZE, UPLOAD_PREFIX
from utils.helpers import new_id


class MediaRepository:
    """Handles R2 operations for media files."""

    def __init__(self, r2_bucket, ctx=None):
        self._r2 = r2_bucket
        self._ctx = ctx

    async def get(self, key: str, options: dict = None):
        if self._r2 is None:
            raise RuntimeError("Media storage is not configured")
        if options is None:
            return await self._r2.get(key)
        return await self._r2.get(key, **options)

    async def upload(
        self,
        user_id: str,
        content_type: str,
        body,
        size: int,
    ) -> str:
        """Upload a file to R2 and return the public URL."""
        if self._r2 is None:
            raise RuntimeError("Media storage is not configured")
        if content_type not in ALLOWED_TYPES:
            raise ValueError(f"Unsupported type. Allowed: {ALLOWED_TYPES}")
        if size > MAX_FILE_SIZE:
            raise ValueError("File too large. Max 5MB")

        ext = content_type.split("/")[-1].replace("jpeg", "jpg")
        key = f"{UPLOAD_PREFIX}/{user_id}/{new_id()}.{ext}"
        js_body = to_js(body)

        await self._r2.put(key, js_body, httpMetadata={"contentType": content_type})
        return key

    async def delete(self, key: str) -> None:
        if self._r2 is None:
            raise RuntimeError("Media storage is not configured")
        await self._r2.delete(key)
