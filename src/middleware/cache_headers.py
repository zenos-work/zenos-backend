"""Phase 11 Step 45 — Cache header strategy middleware."""


def _is_enterprise_subdomain(host: str) -> bool:
    if not host or "." not in host:
        return False
    labels = host.split(".")
    # Apex domains like zenos.com / zenos.work are not tenant subdomains.
    if len(labels) <= 2:
        return False
    sub = labels[0]
    return sub not in ("www", "api", "app", "localhost")


def cache_control_for_request(path: str, method: str, host: str = "") -> str:
    """Return Cache-Control policy for a given request."""
    m = (method or "GET").upper()

    # Never cache mutating methods
    if m in ("POST", "PUT", "PATCH", "DELETE"):
        return "no-store"

    # Enterprise subdomains are always private
    if _is_enterprise_subdomain(host):
        return "private, no-store, must-revalidate"

    # Route-based public caching policies
    if path.startswith("/api/articles/") and m == "GET":
        return "public, max-age=300, s-maxage=3600, stale-while-revalidate=86400"

    if path == "/api/feed" and m == "GET":
        return "public, max-age=60, s-maxage=300"

    if path.startswith("/api/tags") and m == "GET":
        return "public, max-age=120, s-maxage=600"

    if path.startswith("/api/search") and m == "GET":
        return "public, max-age=120, s-maxage=600"

    if path.startswith("/api/rss/") and m == "GET":
        return "public, max-age=1800, s-maxage=3600"

    if path.startswith("/api/organizations/") and m == "GET":
        return "private, no-cache"

    if path.startswith("/media/") and m == "GET":
        return "public, max-age=31536000, immutable"

    # Default for uncategorized GETs
    if m == "GET":
        return "no-cache"

    return "no-store"


def apply_cache_headers(response, path: str, method: str, host: str = ""):
    """Attach Cache-Control header to response and return it."""
    headers = getattr(response, "headers", None)
    if isinstance(headers, dict):
        headers["Cache-Control"] = cache_control_for_request(path, method, host)
        # Set cache tagging for article responses (manual/worker purge model)
        if path.startswith("/api/articles/") and method.upper() == "GET":
            headers.setdefault("cf-cache-tag", "articles")
    return response
