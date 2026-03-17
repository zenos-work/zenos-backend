# Media has no DB queries — data lives in Cloudflare R2.
# R2 operations use env.MEDIA binding directly in MediaRepository.

ALLOWED_TYPES = ("image/jpeg", "image/png", "image/webp", "image/gif")
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
UPLOAD_PREFIX = "uploads"
