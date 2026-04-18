from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.sessions.service import SessionService


async def handle_sessions(request, env, path, method, query, ctx):
    svc = SessionService(env, ctx)
    parts = path.rstrip("/").split("/")
    # /api/users/me/sessions => parts = ['', 'api', 'users', 'me', 'sessions']
    # /api/users/me/sessions/:id => parts[5] = id
    session_id = parts[5] if len(parts) > 5 else None

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    # GET /api/users/me/sessions
    if method == "GET" and not session_id:
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        return json_resp(await svc.list_sessions(uid, page=page, limit=limit))

    # DELETE /api/users/me/sessions/:id
    if method == "DELETE" and session_id:
        try:
            await svc.revoke_session(session_id, uid)
            return json_resp({"status": "revoked"})
        except ValueError as e:
            return error(str(e), 404)

    return error("Not found", 404)
