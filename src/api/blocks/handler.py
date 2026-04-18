from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.blocks.service import BlockService


async def handle_blocks(request, env, path, method, query, ctx):
    svc = BlockService(env, ctx)
    parts = path.rstrip("/").split("/")
    # /api/users/me/blocks => parts: ['', 'api', 'users', 'me', 'blocks']
    # /api/users/me/blocks/:user_id => parts[5]
    # /api/users/me/mutes => parts[4] = 'mutes'
    # /api/users/me/mutes/:user_id => parts[5]
    action = parts[4] if len(parts) > 4 else None
    target_id = parts[5] if len(parts) > 5 else None

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    # ── BLOCKS ──
    if action == "blocks":
        # POST /api/users/me/blocks/:user_id
        if method == "POST" and target_id:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                await svc.block_user(uid, target_id, reason=data.get("reason"))
                return json_resp({"status": "blocked"}, 201)
            except ValueError as e:
                return error(str(e), 409)

        # DELETE /api/users/me/blocks/:user_id
        if method == "DELETE" and target_id:
            await svc.unblock_user(uid, target_id)
            return json_resp({"status": "unblocked"})

        # GET /api/users/me/blocks
        if method == "GET" and not target_id:
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            return json_resp(await svc.list_blocked(uid, page=page, limit=limit))

    # ── MUTES ──
    if action == "mutes":
        # POST /api/users/me/mutes/:user_id
        if method == "POST" and target_id:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                await svc.mute_user(uid, target_id, reason=data.get("reason"))
                return json_resp({"status": "muted"}, 201)
            except ValueError as e:
                return error(str(e), 409)

        # DELETE /api/users/me/mutes/:user_id
        if method == "DELETE" and target_id:
            await svc.unmute_user(uid, target_id)
            return json_resp({"status": "unmuted"})

        # GET /api/users/me/mutes
        if method == "GET" and not target_id:
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            return json_resp(await svc.list_muted(uid, page=page, limit=limit))

    return error("Not found", 404)
