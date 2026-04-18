"""Phase 11 Step 41 — Tenant router middleware.

Extracts subdomain from Host header and resolves org context.
"""

from api.subdomains.repository import SubdomainRepository


async def resolve_tenant(request, env):
    """Resolve org context from Host header subdomain.

    Returns OrgContext dict or None if no subdomain/org found.
    """
    host = request.headers.get("Host", "")
    if not host or "." not in host:
        return None

    subdomain = host.split(".")[0]
    # Skip well-known non-tenant subdomains
    if subdomain in ("www", "api", "app", "localhost"):
        return None

    repo = SubdomainRepository(env.DB)
    org_ctx = await repo.resolve_org(subdomain)
    if not org_ctx or not org_ctx.is_active:
        return None

    return org_ctx.to_dict()
