"""Phase 11 Step 44 — Credential vault handler."""

from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.vault.service import VaultService


async def handle_vault(request, env, path, method, query, ctx):
    svc = VaultService(env, ctx)
    parts = path.rstrip("/").split("/")

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    # path: /api/organizations/:org_id/vault/secrets[/:name_or_action]
    # parts: ['', 'api', 'organizations', ':org_id', 'vault', 'secrets', ...]
    org_id = parts[3] if len(parts) >= 4 else ""

    # ── POST /api/organizations/:id/vault/secrets — store ────
    if method == "POST" and len(parts) == 6 and parts[5] == "secrets":
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.store_secret(
                org_id=org_id,
                name=data.get("name", ""),
                secret_type=data.get("secret_type", "generic"),
                created_by=uid,
                metadata=data.get("metadata", "{}"),
                provider=data.get("provider", "cloudflare"),
                key_ref=data.get("key_ref", ""),
                secret_value=data.get("secret_value", ""),
            )
            return json_resp(result, 201)
        except ValueError as e:
            return error(str(e), 400)
        except PermissionError as e:
            return error(str(e), 429)

    # ── GET /api/organizations/:id/vault/secrets — list ──────
    if method == "GET" and len(parts) == 6 and parts[5] == "secrets":
        items = await svc.list_secrets(org_id)
        return json_resp({"secrets": items})

    # ── DELETE /api/organizations/:id/vault/secrets/:sid ──────
    if method == "DELETE" and len(parts) == 7 and parts[5] == "secrets":
        secret_id = parts[6]
        try:
            result = await svc.revoke_secret(org_id, secret_id)
            return json_resp(result)
        except ValueError as e:
            return error(str(e), 404)

    # ── POST .../secrets/:name/rotate ─────────────────────────
    if method == "POST" and len(parts) == 8 and parts[7] == "rotate":
        name = parts[6]
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.rotate_secret(
                org_id,
                name,
                secret_value=data.get("secret_value", ""),
            )
            return json_resp(result)
        except ValueError as e:
            return error(str(e), 404)
        except PermissionError as e:
            return error(str(e), 429)

    # ── POST .../secrets/:name/test ───────────────────────────
    if method == "POST" and len(parts) == 8 and parts[7] == "test":
        name = parts[6]
        try:
            result = await svc.test_secret(org_id, name)
            return json_resp(result)
        except ValueError as e:
            return error(str(e), 404)

    return error("Not found", 404)
