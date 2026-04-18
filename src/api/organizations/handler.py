from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.organizations.service import OrganizationService


async def handle_organizations(request, env, path, method, query, ctx):
    svc = OrganizationService(env, ctx)
    parts = path.rstrip("/").split("/")
    # /api/organizations => ['', 'api', 'organizations']
    # /api/organizations/:id => parts[3] = id
    # /api/organizations/:id/members => parts[4] = 'members'
    # /api/organizations/:id/members/:uid => parts[5] = uid
    # /api/organizations/:id/teams => parts[4] = 'teams'
    # /api/organizations/:id/teams/:tid/members => parts[5]=tid, parts[6]='members'
    # /api/organizations/:id/teams/:tid/members/:uid => parts[7]=uid
    # /api/organizations/:id/invitations => parts[4] = 'invitations'
    # /api/organizations/:id/invitations/:iid => parts[5] = iid

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    org_id = parts[3] if len(parts) > 3 else None
    sub_resource = parts[4] if len(parts) > 4 else None

    # POST /api/organizations
    if method == "POST" and not org_id:
        body = await request.json()
        name = body.get("name")
        if not name:
            return error("name is required", 400)
        result = await svc.create_org(uid, name, body.get("description"))
        return json_resp(result, 201)

    # GET /api/organizations (list user's orgs)
    if method == "GET" and not org_id:
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        return json_resp(await svc.list_user_orgs(uid, page=page, limit=limit))

    if not org_id:
        return error("Not found", 404)

    # ── Members ────────────────────────────────────────────────────────
    if sub_resource == "members":
        target_uid = parts[5] if len(parts) > 5 else None

        if method == "GET" and not target_uid:
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            try:
                return json_resp(
                    await svc.list_members(org_id, uid, page=page, limit=limit)
                )
            except PermissionError as e:
                return error(str(e), 403)

        if method == "POST" and not target_uid:
            body = await request.json()
            try:
                result = await svc.add_member(
                    org_id, uid, body.get("user_id"), body.get("role", "member")
                )
                return json_resp(result, 201)
            except PermissionError as e:
                return error(str(e), 403)
            except ValueError as e:
                return error(str(e), 400)

        if method == "PUT" and target_uid:
            body = await request.json()
            try:
                return json_resp(
                    await svc.update_member_role(
                        org_id, uid, target_uid, body.get("role")
                    )
                )
            except PermissionError as e:
                return error(str(e), 403)
            except ValueError as e:
                return error(str(e), 400)

        if method == "DELETE" and target_uid:
            try:
                await svc.remove_member(org_id, uid, target_uid)
                return json_resp({"status": "removed"})
            except PermissionError as e:
                return error(str(e), 403)
            except ValueError as e:
                return error(str(e), 400)

        return error("Not found", 404)

    # ── Teams ──────────────────────────────────────────────────────────
    if sub_resource == "teams":
        team_id = parts[5] if len(parts) > 5 else None
        team_sub = parts[6] if len(parts) > 6 else None
        team_member_uid = parts[7] if len(parts) > 7 else None

        if method == "POST" and not team_id:
            body = await request.json()
            try:
                result = await svc.create_team(
                    org_id, uid, body.get("name"), body.get("description")
                )
                return json_resp(result, 201)
            except PermissionError as e:
                return error(str(e), 403)

        if method == "GET" and not team_id:
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            try:
                return json_resp(
                    await svc.list_teams(org_id, uid, page=page, limit=limit)
                )
            except PermissionError as e:
                return error(str(e), 403)

        if team_id and team_sub == "members":
            if method == "POST" and not team_member_uid:
                body = await request.json()
                try:
                    result = await svc.add_team_member(
                        org_id, uid, team_id, body.get("user_id")
                    )
                    return json_resp(result, 201)
                except PermissionError as e:
                    return error(str(e), 403)

            if method == "DELETE" and team_member_uid:
                try:
                    await svc.remove_team_member(org_id, uid, team_id, team_member_uid)
                    return json_resp({"status": "removed"})
                except PermissionError as e:
                    return error(str(e), 403)

        return error("Not found", 404)

    # ── Invitations ────────────────────────────────────────────────────
    if sub_resource == "invitations":
        inv_id = parts[5] if len(parts) > 5 else None

        if method == "POST" and not inv_id:
            body = await request.json()
            try:
                result = await svc.create_invitation(
                    org_id, uid, body.get("email"), body.get("role", "member")
                )
                return json_resp(result, 201)
            except PermissionError as e:
                return error(str(e), 403)
            except ValueError as e:
                return error(str(e), 400)

        if method == "GET" and not inv_id:
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            try:
                return json_resp(
                    await svc.list_invitations(org_id, uid, page=page, limit=limit)
                )
            except PermissionError as e:
                return error(str(e), 403)

        if method == "DELETE" and inv_id:
            try:
                await svc.delete_invitation(org_id, uid, inv_id)
                return json_resp({"status": "deleted"})
            except PermissionError as e:
                return error(str(e), 403)

        return error("Not found", 404)

    # ── Org detail ─────────────────────────────────────────────────────
    if method == "GET" and org_id and not sub_resource:
        try:
            return json_resp(await svc.get_org(org_id, uid))
        except PermissionError as e:
            return error(str(e), 403)
        except ValueError as e:
            return error(str(e), 404)

    if method == "PUT" and org_id and not sub_resource:
        body = await request.json()
        try:
            return json_resp(
                await svc.update_org(
                    org_id,
                    uid,
                    body.get("name"),
                    body.get("description"),
                    body.get("logo_url"),
                    body.get("website"),
                )
            )
        except PermissionError as e:
            return error(str(e), 403)
        except ValueError as e:
            return error(str(e), 404)

    return error("Not found", 404)


async def handle_invitation_accept(request, env, path, method, query, ctx):
    """POST /api/invitations/:token/accept"""
    svc = OrganizationService(env, ctx)
    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    parts = path.rstrip("/").split("/")
    token = parts[3] if len(parts) > 3 else None
    if method == "POST" and token:
        try:
            result = await svc.accept_invitation(token, user["sub"])
            return json_resp(result, 200)
        except ValueError as e:
            return error(str(e), 400)
    return error("Not found", 404)
