"""Phase 5 Step 25 — Lead-generation service."""

from api.leads.repository import LeadRepository
from utils.helpers import new_id, paginate


class LeadService:
    def __init__(self, env, ctx=None):
        self._repo = LeadRepository(env.DB, ctx)

    # ── Lead Capture Forms ───────────────────────────────────
    async def list_forms(self, org_id):
        items = await self._repo.list_forms(org_id)
        return [f.to_dict() for f in items]

    async def get_form(self, fid):
        f = await self._repo.get_form(fid)
        if not f:
            raise ValueError("Form not found")
        return f.to_dict()

    async def create_form(
        self,
        org_id,
        owner_id,
        name,
        slug,
        description="",
        placement="inline",
        fields_schema=None,
        submit_button_text="Subscribe",
        success_message="",
        redirect_url="",
        tags_on_submit=None,
        workflow_id="",
    ):
        fid = new_id()
        await self._repo.create_form(
            fid,
            org_id,
            owner_id,
            name,
            slug,
            description,
            placement,
            fields_schema or {},
            submit_button_text,
            success_message,
            redirect_url,
            tags_on_submit or [],
            workflow_id,
            True,
        )
        return {"id": fid}

    async def update_form(self, fid, **kwargs):
        existing = await self._repo.get_form(fid)
        if not existing:
            raise ValueError("Form not found")
        await self._repo.update_form(
            fid,
            kwargs.get("name") or existing.name,
            kwargs.get("description")
            if kwargs.get("description") is not None
            else existing.description,
            kwargs.get("placement") or existing.placement,
            kwargs.get("fields_schema")
            if kwargs.get("fields_schema") is not None
            else existing.fields_schema,
            kwargs.get("submit_button_text") or existing.submit_button_text,
            kwargs.get("success_message")
            if kwargs.get("success_message") is not None
            else existing.success_message,
            kwargs.get("redirect_url")
            if kwargs.get("redirect_url") is not None
            else existing.redirect_url,
            kwargs.get("tags_on_submit")
            if kwargs.get("tags_on_submit") is not None
            else existing.tags_on_submit,
            kwargs.get("workflow_id")
            if kwargs.get("workflow_id") is not None
            else existing.workflow_id,
            kwargs.get("is_active")
            if kwargs.get("is_active") is not None
            else existing.is_active,
        )
        return {"id": fid}

    async def delete_form(self, fid):
        existing = await self._repo.get_form(fid)
        if not existing:
            raise ValueError("Form not found")
        await self._repo.delete_form(fid)

    # ── Leads ────────────────────────────────────────────────
    async def list_leads(self, org_id, status=None, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_leads(org_id, status, lim, off)
        return {"leads": [lead.to_dict() for lead in items], "page": page, "limit": lim}

    async def get_lead(self, lid):
        lead = await self._repo.get_lead(lid)
        if not lead:
            raise ValueError("Lead not found")
        return lead.to_dict(scope="admin")

    async def create_lead(self, org_id, email, **kwargs):
        lid = new_id()
        await self._repo.create_lead(
            lid,
            org_id,
            email,
            kwargs.get("first_name", ""),
            kwargs.get("last_name", ""),
            kwargs.get("company", ""),
            kwargs.get("job_title", ""),
            kwargs.get("phone", ""),
            kwargs.get("source", ""),
            kwargs.get("source_detail", ""),
            kwargs.get("utm_source", ""),
            kwargs.get("utm_medium", ""),
            kwargs.get("utm_campaign", ""),
            kwargs.get("utm_term", ""),
            kwargs.get("utm_content", ""),
            kwargs.get("referrer_url", ""),
            kwargs.get("landing_page", ""),
            kwargs.get("capture_form_id", ""),
            kwargs.get("custom_fields", {}),
            kwargs.get("consent_email", False),
            kwargs.get("consent_tracking", False),
            kwargs.get("consent_at", ""),
            kwargs.get("ip_address", ""),
            kwargs.get("user_agent", ""),
        )
        # Increment form submission count if from a form
        if kwargs.get("capture_form_id"):
            await self._repo.inc_form_submissions(kwargs["capture_form_id"])
        return {"id": lid}

    async def update_lead(self, lid, **kwargs):
        existing = await self._repo.get_lead(lid)
        if not existing:
            raise ValueError("Lead not found")
        await self._repo.update_lead(
            lid,
            kwargs.get("first_name") or existing.first_name,
            kwargs.get("last_name") or existing.last_name,
            kwargs.get("company") or existing.company,
            kwargs.get("job_title") or existing.job_title,
            kwargs.get("status") or existing.status,
            kwargs.get("custom_fields")
            if kwargs.get("custom_fields") is not None
            else existing.custom_fields,
        )
        return {"id": lid}

    async def delete_lead(self, lid):
        existing = await self._repo.get_lead(lid)
        if not existing:
            raise ValueError("Lead not found")
        await self._repo.delete_lead(lid)

    # ── Lead Tags ────────────────────────────────────────────
    async def list_lead_tags(self, org_id, lead_id):
        return await self._repo.list_lead_tags(org_id, lead_id)

    async def add_lead_tag(self, org_id, lead_id, tag):
        await self._repo.add_lead_tag(org_id, lead_id, tag)

    async def remove_lead_tag(self, org_id, lead_id, tag):
        await self._repo.remove_lead_tag(org_id, lead_id, tag)

    # ── Lead Events ──────────────────────────────────────────
    async def list_lead_events(self, lead_id, page=1, limit=50):
        lim, off = paginate(page, limit)
        items = await self._repo.list_lead_events(lead_id, lim, off)
        return {"events": [e.to_dict() for e in items], "page": page, "limit": lim}

    async def create_lead_event(
        self, lead_id, org_id, event_type, metadata=None, actor_id=""
    ):
        eid = new_id()
        await self._repo.create_lead_event(
            eid, lead_id, org_id, event_type, metadata or {}, actor_id
        )
        return {"id": eid}

    # ── Lead Score Rules ─────────────────────────────────────
    async def list_score_rules(self, org_id):
        items = await self._repo.list_score_rules(org_id)
        return [r.to_dict() for r in items]

    async def create_score_rule(
        self, org_id, name, trigger_event, condition=None, score_delta=0, is_active=True
    ):
        rid = new_id()
        await self._repo.create_score_rule(
            rid,
            org_id,
            name,
            trigger_event,
            condition or {},
            score_delta,
            is_active,
        )
        return {"id": rid}

    async def update_score_rule(self, rid, **kwargs):
        existing = await self._repo.get_score_rule(rid)
        if not existing:
            raise ValueError("Score rule not found")
        await self._repo.update_score_rule(
            rid,
            kwargs.get("name") or existing.name,
            kwargs.get("trigger_event") or existing.trigger_event,
            kwargs.get("condition")
            if kwargs.get("condition") is not None
            else existing.condition,
            kwargs.get("score_delta")
            if kwargs.get("score_delta") is not None
            else existing.score_delta,
            kwargs.get("is_active")
            if kwargs.get("is_active") is not None
            else existing.is_active,
        )
        return {"id": rid}

    async def delete_score_rule(self, rid):
        await self._repo.delete_score_rule(rid)

    # ── Lead Pipelines ───────────────────────────────────────
    async def list_pipelines(self, org_id):
        items = await self._repo.list_pipelines(org_id)
        return [p.to_dict() for p in items]

    async def get_pipeline(self, pid):
        p = await self._repo.get_pipeline(pid)
        if not p:
            raise ValueError("Pipeline not found")
        return p.to_dict()

    async def create_pipeline(self, org_id, name, description="", sort_order=0):
        pid = new_id()
        await self._repo.create_pipeline(pid, org_id, name, description, sort_order)
        return {"id": pid}

    async def update_pipeline(self, pid, **kwargs):
        existing = await self._repo.get_pipeline(pid)
        if not existing:
            raise ValueError("Pipeline not found")
        await self._repo.update_pipeline(
            pid,
            kwargs.get("name") or existing.name,
            kwargs.get("description")
            if kwargs.get("description") is not None
            else existing.description,
            kwargs.get("sort_order")
            if kwargs.get("sort_order") is not None
            else existing.sort_order,
        )
        return {"id": pid}

    async def delete_pipeline(self, pid):
        existing = await self._repo.get_pipeline(pid)
        if not existing:
            raise ValueError("Pipeline not found")
        await self._repo.delete_pipeline(pid)

    # ── Pipeline Stages ──────────────────────────────────────
    async def list_stages(self, pipeline_id):
        items = await self._repo.list_stages(pipeline_id)
        return [s.to_dict() for s in items]

    async def create_stage(
        self, pipeline_id, name, sort_order=0, stage_type="open", color=""
    ):
        sid = new_id()
        await self._repo.create_stage(
            sid, pipeline_id, name, sort_order, stage_type, color
        )
        return {"id": sid}

    async def update_stage(self, sid, **kwargs):
        existing = await self._repo.get_stage(sid)
        if not existing:
            raise ValueError("Stage not found")
        await self._repo.update_stage(
            sid,
            kwargs.get("name") or existing.name,
            kwargs.get("sort_order")
            if kwargs.get("sort_order") is not None
            else existing.sort_order,
            kwargs.get("stage_type") or existing.stage_type,
            kwargs.get("color") if kwargs.get("color") is not None else existing.color,
        )
        return {"id": sid}

    async def delete_stage(self, sid):
        await self._repo.delete_stage(sid)

    # ── Lead Pipeline Entries ────────────────────────────────
    async def list_pipeline_entries(self, pipeline_id, page=1, limit=50):
        lim, off = paginate(page, limit)
        items = await self._repo.list_pipeline_entries(pipeline_id, lim, off)
        return {"entries": [e.to_dict() for e in items], "page": page, "limit": lim}

    async def create_pipeline_entry(
        self, lead_id, pipeline_id, stage_id, assigned_to="", deal_value=0, notes=""
    ):
        eid = new_id()
        await self._repo.create_pipeline_entry(
            eid,
            lead_id,
            pipeline_id,
            stage_id,
            assigned_to,
            deal_value,
            notes,
        )
        return {"id": eid}

    async def update_pipeline_entry(self, eid, **kwargs):
        existing = await self._repo.get_pipeline_entry(eid)
        if not existing:
            raise ValueError("Pipeline entry not found")
        await self._repo.update_pipeline_entry(
            eid,
            kwargs.get("stage_id") or existing.stage_id,
            kwargs.get("assigned_to")
            if kwargs.get("assigned_to") is not None
            else existing.assigned_to,
            kwargs.get("deal_value")
            if kwargs.get("deal_value") is not None
            else existing.deal_value,
            kwargs.get("notes") if kwargs.get("notes") is not None else existing.notes,
        )
        return {"id": eid}

    async def delete_pipeline_entry(self, eid):
        await self._repo.delete_pipeline_entry(eid)

    # ── Email Sequences ──────────────────────────────────────
    async def list_sequences(self, org_id):
        items = await self._repo.list_sequences(org_id)
        return [s.to_dict() for s in items]

    async def get_sequence(self, sid):
        s = await self._repo.get_sequence(sid)
        if not s:
            raise ValueError("Sequence not found")
        return s.to_dict()

    async def create_sequence(
        self, org_id, name, description="", trigger_type="", created_by=""
    ):
        sid = new_id()
        await self._repo.create_sequence(
            sid, org_id, name, description, trigger_type, created_by
        )
        return {"id": sid}

    async def update_sequence(self, sid, **kwargs):
        existing = await self._repo.get_sequence(sid)
        if not existing:
            raise ValueError("Sequence not found")
        await self._repo.update_sequence(
            sid,
            kwargs.get("name") or existing.name,
            kwargs.get("description")
            if kwargs.get("description") is not None
            else existing.description,
            kwargs.get("trigger_type") or existing.trigger_type,
            kwargs.get("status") or existing.status,
        )
        return {"id": sid}

    async def delete_sequence(self, sid):
        existing = await self._repo.get_sequence(sid)
        if not existing:
            raise ValueError("Sequence not found")
        await self._repo.delete_sequence(sid)

    # ── Email Sequence Steps ─────────────────────────────────
    async def list_steps(self, sequence_id):
        items = await self._repo.list_steps(sequence_id)
        return [s.to_dict() for s in items]

    async def create_step(
        self,
        sequence_id,
        step_number,
        delay_days=0,
        subject="",
        body_html="",
        body_text="",
    ):
        step_id = new_id()
        await self._repo.create_step(
            step_id, sequence_id, step_number, delay_days, subject, body_html, body_text
        )
        return {"id": step_id}

    async def update_step(self, step_id, **kwargs):
        existing = await self._repo.get_step(step_id)
        if not existing:
            raise ValueError("Step not found")
        await self._repo.update_step(
            step_id,
            kwargs.get("delay_days")
            if kwargs.get("delay_days") is not None
            else existing.delay_days,
            kwargs.get("subject") or existing.subject,
            kwargs.get("body_html")
            if kwargs.get("body_html") is not None
            else existing.body_html,
            kwargs.get("body_text")
            if kwargs.get("body_text") is not None
            else existing.body_text,
        )
        return {"id": step_id}

    async def delete_step(self, step_id):
        await self._repo.delete_step(step_id)

    # ── Lead Sequence Enrollments ────────────────────────────
    async def list_enrollments(self, sequence_id, page=1, limit=50):
        lim, off = paginate(page, limit)
        items = await self._repo.list_enrollments(sequence_id, lim, off)
        return {"enrollments": [e.to_dict() for e in items], "page": page, "limit": lim}

    async def create_enrollment(self, lead_id, sequence_id):
        eid = new_id()
        await self._repo.create_enrollment(eid, lead_id, sequence_id)
        return {"id": eid}

    async def update_enrollment(self, eid, current_step=None, status=None):
        existing = await self._repo.get_enrollment(eid)
        if not existing:
            raise ValueError("Enrollment not found")
        await self._repo.update_enrollment(
            eid,
            current_step if current_step is not None else existing.current_step,
            status or existing.status,
        )
        return {"id": eid}
