"""Phase 11 Step 42 — SSO handler (SAML + OIDC)."""

from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.sso.service import SsoService


async def handle_sso(request, env, path, method, query, ctx):
    svc = SsoService(env, ctx)
    parts = path.rstrip("/").split("/")

    # ── SAML endpoints (public — IdP callbacks) ──────────────
    # GET /api/auth/sso/saml/:org_id/metadata
    if "/saml/" in path and path.endswith("/metadata") and method == "GET":
        org_id = parts[-2] if len(parts) >= 2 else ""
        try:
            xml = await svc.saml_metadata(org_id)
            return json_resp({"metadata": xml})
        except ValueError as e:
            return error(str(e), 404)

    # GET /api/auth/sso/saml/:org_id/login
    if "/saml/" in path and path.endswith("/login") and method == "GET":
        org_id = parts[-2] if len(parts) >= 2 else ""
        try:
            result = await svc.saml_login_url(org_id)
            return json_resp(result)
        except ValueError as e:
            return error(str(e), 404)

    # POST /api/auth/sso/saml/:org_id/acs
    if "/saml/" in path and path.endswith("/acs") and method == "POST":
        org_id = parts[-2] if len(parts) >= 2 else ""
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.saml_acs(
                org_id,
                saml_response=data.get("SAMLResponse", ""),
                relay_state=data.get("RelayState", ""),
            )
            return json_resp(result)
        except ValueError as e:
            return error(str(e), 400)

    # ── OIDC endpoints ───────────────────────────────────────
    # GET /api/auth/sso/oidc/:org_id/authorize
    if "/oidc/" in path and path.endswith("/authorize") and method == "GET":
        org_id = parts[-2] if len(parts) >= 2 else ""
        redirect_url = query.get("redirect_url", [""])[0] if query else ""
        try:
            result = await svc.oidc_authorize_url(org_id, redirect_url)
            return json_resp(result)
        except ValueError as e:
            return error(str(e), 404)

    # GET /api/auth/sso/oidc/:org_id/callback
    if "/oidc/" in path and path.endswith("/callback") and method == "GET":
        org_id = parts[-2] if len(parts) >= 2 else ""
        state = query.get("state", [""])[0] if query else ""
        code = query.get("code", [""])[0] if query else ""
        try:
            result = await svc.oidc_callback(org_id, state, code)
            return json_resp(result)
        except ValueError as e:
            return error(str(e), 400)

    # ── Config management (auth required) ────────────────────
    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)

    # GET /api/organizations/:id/sso/configs
    if path.endswith("/configs") and method == "GET":
        org_id = parts[3] if len(parts) >= 5 else ""
        configs = await svc.list_configs(org_id)
        return json_resp({"configs": configs})

    # POST /api/organizations/:id/sso/configs
    if path.endswith("/configs") and method == "POST":
        org_id = parts[3] if len(parts) >= 5 else ""
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.create_config(org_id, data)
            return json_resp(result, 201)
        except ValueError as e:
            return error(str(e), 400)

    # PUT /api/organizations/:id/sso/configs/:config_id
    if "/configs/" in path and method == "PUT":
        config_id = parts[-1]
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.update_config(config_id, data)
            return json_resp(result)
        except ValueError as e:
            return error(str(e), 400)

    # DELETE /api/organizations/:id/sso/configs/:config_id
    if "/configs/" in path and method == "DELETE":
        config_id = parts[-1]
        result = await svc.delete_config(config_id)
        return json_resp(result)

    return error("Not found", 404)
