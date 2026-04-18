"""Phase 5 Step 25 — Lead-generation handler."""

from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.leads.service import LeadService
from api.feature_flags.service import FeatureFlagService


async def _is_feature_enabled(env, ctx, user, flag_key: str) -> bool:
    if getattr(env, "DB", None) is None:
        return True
    try:
        svc = FeatureFlagService(env, ctx)
        return await svc.evaluate_one(
            flag_key,
            user_id=user.get("sub"),
            user_role=user.get("role", ""),
        )
    except Exception:
        return False


async def handle_leads(request, env, path, method, query, ctx):
    svc = LeadService(env, ctx)
    parts = path.rstrip("/").split("/")

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    if not await _is_feature_enabled(env, ctx, user, "leads"):
        return error("Feature 'leads' is disabled", 403)

    # ── Lead Capture Forms ───────────────────────────────────
    if path.startswith("/api/leads/forms"):
        org_id = query.get("org_id", [None])[0]
        # GET /api/leads/forms
        if method == "GET" and len(parts) == 4:
            if not org_id:
                return error("org_id required", 400)
            return json_resp({"forms": await svc.list_forms(org_id)})
        # GET /api/leads/forms/:id
        if method == "GET" and len(parts) == 5:
            try:
                return json_resp(await svc.get_form(parts[4]))
            except ValueError as e:
                return error(str(e), 404)
        # POST /api/leads/forms
        if method == "POST" and len(parts) == 4:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_form(
                    org_id=data.get("org_id", ""),
                    owner_id=uid,
                    name=data.get("name", ""),
                    slug=data.get("slug", ""),
                    description=data.get("description", ""),
                    placement=data.get("placement", "inline"),
                    fields_schema=data.get("fields_schema"),
                    submit_button_text=data.get("submit_button_text", "Subscribe"),
                    success_message=data.get("success_message", ""),
                    redirect_url=data.get("redirect_url", ""),
                    tags_on_submit=data.get("tags_on_submit"),
                    workflow_id=data.get("workflow_id", ""),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # PUT /api/leads/forms/:id
        if method == "PUT" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.update_form(parts[4], **data)
                return json_resp(result)
            except ValueError as e:
                return error(str(e), 400)
        # DELETE /api/leads/forms/:id
        if method == "DELETE" and len(parts) == 5:
            try:
                await svc.delete_form(parts[4])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Score Rules ──────────────────────────────────────────
    if path.startswith("/api/leads/score-rules"):
        org_id = query.get("org_id", [None])[0]
        # GET /api/leads/score-rules
        if method == "GET" and len(parts) == 4:
            if not org_id:
                return error("org_id required", 400)
            return json_resp({"rules": await svc.list_score_rules(org_id)})
        # POST /api/leads/score-rules
        if method == "POST" and len(parts) == 4:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_score_rule(
                    org_id=data.get("org_id", ""),
                    name=data.get("name", ""),
                    trigger_event=data.get("trigger_event", ""),
                    condition=data.get("condition"),
                    score_delta=data.get("score_delta", 0),
                    is_active=data.get("is_active", True),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # PUT /api/leads/score-rules/:id
        if method == "PUT" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.update_score_rule(parts[4], **data)
                return json_resp(result)
            except ValueError as e:
                return error(str(e), 400)
        # DELETE /api/leads/score-rules/:id
        if method == "DELETE" and len(parts) == 5:
            await svc.delete_score_rule(parts[4])
            return json_resp({"deleted": True})
        return error("Not found", 404)

    # ── Pipelines ────────────────────────────────────────────
    if path.startswith("/api/leads/pipelines"):
        org_id = query.get("org_id", [None])[0]

        # Stages sub-resource: /api/leads/pipelines/:pid/stages[/:sid]
        if len(parts) >= 6 and parts[5] == "stages":
            pipeline_id = parts[4]
            # GET /api/leads/pipelines/:pid/stages
            if method == "GET" and len(parts) == 6:
                return json_resp({"stages": await svc.list_stages(pipeline_id)})
            # POST /api/leads/pipelines/:pid/stages
            if method == "POST" and len(parts) == 6:
                body = await request.json()
                data = body if isinstance(body, dict) else {}
                try:
                    result = await svc.create_stage(
                        pipeline_id,
                        name=data.get("name", ""),
                        sort_order=data.get("sort_order", 0),
                        stage_type=data.get("stage_type", "open"),
                        color=data.get("color", ""),
                    )
                    return json_resp(result, 201)
                except ValueError as e:
                    return error(str(e), 400)
            # PUT /api/leads/pipelines/:pid/stages/:sid
            if method == "PUT" and len(parts) == 7:
                body = await request.json()
                data = body if isinstance(body, dict) else {}
                try:
                    result = await svc.update_stage(parts[6], **data)
                    return json_resp(result)
                except ValueError as e:
                    return error(str(e), 400)
            # DELETE /api/leads/pipelines/:pid/stages/:sid
            if method == "DELETE" and len(parts) == 7:
                await svc.delete_stage(parts[6])
                return json_resp({"deleted": True})
            return error("Not found", 404)

        # Entries sub-resource: /api/leads/pipelines/:pid/entries[/:eid]
        if len(parts) >= 6 and parts[5] == "entries":
            pipeline_id = parts[4]
            # GET /api/leads/pipelines/:pid/entries
            if method == "GET" and len(parts) == 6:
                page = int(query.get("page", ["1"])[0])
                limit = int(query.get("limit", ["50"])[0])
                return json_resp(
                    await svc.list_pipeline_entries(pipeline_id, page, limit)
                )
            # POST /api/leads/pipelines/:pid/entries
            if method == "POST" and len(parts) == 6:
                body = await request.json()
                data = body if isinstance(body, dict) else {}
                try:
                    result = await svc.create_pipeline_entry(
                        lead_id=data.get("lead_id", ""),
                        pipeline_id=pipeline_id,
                        stage_id=data.get("stage_id", ""),
                        assigned_to=data.get("assigned_to", ""),
                        deal_value=data.get("deal_value", 0),
                        notes=data.get("notes", ""),
                    )
                    return json_resp(result, 201)
                except ValueError as e:
                    return error(str(e), 400)
            # PUT /api/leads/pipelines/:pid/entries/:eid
            if method == "PUT" and len(parts) == 7:
                body = await request.json()
                data = body if isinstance(body, dict) else {}
                try:
                    result = await svc.update_pipeline_entry(parts[6], **data)
                    return json_resp(result)
                except ValueError as e:
                    return error(str(e), 400)
            # DELETE /api/leads/pipelines/:pid/entries/:eid
            if method == "DELETE" and len(parts) == 7:
                await svc.delete_pipeline_entry(parts[6])
                return json_resp({"deleted": True})
            return error("Not found", 404)

        # GET /api/leads/pipelines
        if method == "GET" and len(parts) == 4:
            if not org_id:
                return error("org_id required", 400)
            return json_resp({"pipelines": await svc.list_pipelines(org_id)})
        # GET /api/leads/pipelines/:id
        if method == "GET" and len(parts) == 5:
            try:
                return json_resp(await svc.get_pipeline(parts[4]))
            except ValueError as e:
                return error(str(e), 404)
        # POST /api/leads/pipelines
        if method == "POST" and len(parts) == 4:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_pipeline(
                    org_id=data.get("org_id", ""),
                    name=data.get("name", ""),
                    description=data.get("description", ""),
                    sort_order=data.get("sort_order", 0),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # PUT /api/leads/pipelines/:id
        if method == "PUT" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.update_pipeline(parts[4], **data)
                return json_resp(result)
            except ValueError as e:
                return error(str(e), 400)
        # DELETE /api/leads/pipelines/:id
        if method == "DELETE" and len(parts) == 5:
            try:
                await svc.delete_pipeline(parts[4])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Email Sequences ──────────────────────────────────────
    if path.startswith("/api/leads/sequences"):
        org_id = query.get("org_id", [None])[0]

        # Steps sub-resource: /api/leads/sequences/:sid/steps[/:step_id]
        if len(parts) >= 6 and parts[5] == "steps":
            sequence_id = parts[4]
            if method == "GET" and len(parts) == 6:
                return json_resp({"steps": await svc.list_steps(sequence_id)})
            if method == "POST" and len(parts) == 6:
                body = await request.json()
                data = body if isinstance(body, dict) else {}
                try:
                    result = await svc.create_step(
                        sequence_id,
                        step_number=data.get("step_number", 0),
                        delay_days=data.get("delay_days", 0),
                        subject=data.get("subject", ""),
                        body_html=data.get("body_html", ""),
                        body_text=data.get("body_text", ""),
                    )
                    return json_resp(result, 201)
                except ValueError as e:
                    return error(str(e), 400)
            if method == "PUT" and len(parts) == 7:
                body = await request.json()
                data = body if isinstance(body, dict) else {}
                try:
                    result = await svc.update_step(parts[6], **data)
                    return json_resp(result)
                except ValueError as e:
                    return error(str(e), 400)
            if method == "DELETE" and len(parts) == 7:
                await svc.delete_step(parts[6])
                return json_resp({"deleted": True})
            return error("Not found", 404)

        # Enrollments sub-resource: /api/leads/sequences/:sid/enrollments[/:eid]
        if len(parts) >= 6 and parts[5] == "enrollments":
            sequence_id = parts[4]
            if method == "GET" and len(parts) == 6:
                page = int(query.get("page", ["1"])[0])
                limit = int(query.get("limit", ["50"])[0])
                return json_resp(await svc.list_enrollments(sequence_id, page, limit))
            if method == "POST" and len(parts) == 6:
                body = await request.json()
                data = body if isinstance(body, dict) else {}
                try:
                    result = await svc.create_enrollment(
                        lead_id=data.get("lead_id", ""),
                        sequence_id=sequence_id,
                    )
                    return json_resp(result, 201)
                except ValueError as e:
                    return error(str(e), 400)
            if method == "PUT" and len(parts) == 7:
                body = await request.json()
                data = body if isinstance(body, dict) else {}
                try:
                    result = await svc.update_enrollment(
                        parts[6],
                        current_step=data.get("current_step"),
                        status=data.get("status"),
                    )
                    return json_resp(result)
                except ValueError as e:
                    return error(str(e), 400)
            return error("Not found", 404)

        # GET /api/leads/sequences
        if method == "GET" and len(parts) == 4:
            if not org_id:
                return error("org_id required", 400)
            return json_resp({"sequences": await svc.list_sequences(org_id)})
        # GET /api/leads/sequences/:id
        if method == "GET" and len(parts) == 5:
            try:
                return json_resp(await svc.get_sequence(parts[4]))
            except ValueError as e:
                return error(str(e), 404)
        # POST /api/leads/sequences
        if method == "POST" and len(parts) == 4:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_sequence(
                    org_id=data.get("org_id", ""),
                    name=data.get("name", ""),
                    description=data.get("description", ""),
                    trigger_type=data.get("trigger_type", ""),
                    created_by=uid,
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # PUT /api/leads/sequences/:id
        if method == "PUT" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.update_sequence(parts[4], **data)
                return json_resp(result)
            except ValueError as e:
                return error(str(e), 400)
        # DELETE /api/leads/sequences/:id
        if method == "DELETE" and len(parts) == 5:
            try:
                await svc.delete_sequence(parts[4])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Lead CRUD ────────────────────────────────────────────
    org_id = query.get("org_id", [None])[0]

    # Lead tags sub-resource: /api/leads/:lid/tags
    if len(parts) >= 5 and parts[4] == "tags":
        lead_id = parts[3]
        lead_org = query.get("org_id", [None])[0]
        if not lead_org:
            return error("org_id required", 400)
        if method == "GET":
            tags = await svc.list_lead_tags(lead_org, lead_id)
            return json_resp({"tags": tags})
        if method == "POST":
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            await svc.add_lead_tag(lead_org, lead_id, data.get("tag", ""))
            return json_resp({"added": True}, 201)
        if method == "DELETE" and len(parts) == 6:
            await svc.remove_lead_tag(lead_org, lead_id, parts[5])
            return json_resp({"deleted": True})
        return error("Not found", 404)

    # Lead events sub-resource: /api/leads/:lid/events
    if len(parts) >= 5 and parts[4] == "events":
        lead_id = parts[3]
        if method == "GET":
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["50"])[0])
            return json_resp(await svc.list_lead_events(lead_id, page, limit))
        if method == "POST":
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_lead_event(
                    lead_id,
                    data.get("org_id", ""),
                    data.get("event_type", ""),
                    metadata=data.get("metadata"),
                    actor_id=uid,
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        return error("Not found", 404)

    # GET /api/leads
    if path.rstrip("/") == "/api/leads" and method == "GET":
        if not org_id:
            return error("org_id required", 400)
        status = query.get("status", [None])[0]
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        return json_resp(await svc.list_leads(org_id, status, page, limit))

    # POST /api/leads
    if path.rstrip("/") == "/api/leads" and method == "POST":
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.create_lead(
                org_id=data.get("org_id", ""),
                email=data.get("email", ""),
                **{k: v for k, v in data.items() if k not in ("org_id", "email")},
            )
            return json_resp(result, 201)
        except ValueError as e:
            return error(str(e), 400)

    # GET /api/leads/:id
    if len(parts) == 4 and method == "GET":
        try:
            return json_resp(await svc.get_lead(parts[3]))
        except ValueError as e:
            return error(str(e), 404)

    # PUT /api/leads/:id
    if len(parts) == 4 and method == "PUT":
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.update_lead(parts[3], **data)
            return json_resp(result)
        except ValueError as e:
            return error(str(e), 400)

    # DELETE /api/leads/:id
    if len(parts) == 4 and method == "DELETE":
        try:
            await svc.delete_lead(parts[3])
            return json_resp({"deleted": True})
        except ValueError as e:
            return error(str(e), 404)

    return error("Not found", 404)
