"""Phase 5 Step 25 — Lead-generation repository."""

import json
from db.repository import BaseRepository
from api.leads import queries as Q
from models.lead.model import (
    LeadCaptureForm,
    Lead,
    LeadEvent,
    LeadScoreRule,
    LeadPipeline,
    PipelineStage,
    LeadPipelineEntry,
    EmailSequence,
    EmailSequenceStep,
    LeadSequenceEnrollment,
)


class LeadRepository(BaseRepository):
    def _one(self, cls, row):
        return self.map_one(row, cls)

    def _many(self, rows, cls):
        return self.map_many(rows, cls)

    # ── Lead Capture Forms ───────────────────────────────────
    async def list_forms(self, org_id):
        return self._many(await self.find_all(Q.LIST_FORMS, org_id), LeadCaptureForm)

    async def get_form(self, fid):
        return self._one(LeadCaptureForm, await self.find_one(Q.GET_FORM, fid))

    async def create_form(
        self,
        fid,
        org_id,
        owner_id,
        name,
        slug,
        description,
        placement,
        fields_schema,
        submit_button_text,
        success_message,
        redirect_url,
        tags_on_submit,
        workflow_id,
        is_active,
    ):
        await self.execute(
            Q.INSERT_FORM,
            fid,
            org_id,
            owner_id,
            name,
            slug,
            description,
            placement,
            json.dumps(fields_schema),
            submit_button_text,
            success_message,
            redirect_url,
            json.dumps(tags_on_submit),
            workflow_id,
            int(is_active),
        )

    async def update_form(
        self,
        fid,
        name,
        description,
        placement,
        fields_schema,
        submit_button_text,
        success_message,
        redirect_url,
        tags_on_submit,
        workflow_id,
        is_active,
    ):
        await self.execute(
            Q.UPDATE_FORM,
            name,
            description,
            placement,
            json.dumps(fields_schema),
            submit_button_text,
            success_message,
            redirect_url,
            json.dumps(tags_on_submit),
            workflow_id,
            int(is_active),
            fid,
        )

    async def delete_form(self, fid):
        await self.execute(Q.DELETE_FORM, fid)

    async def inc_form_submissions(self, fid):
        await self.execute(Q.INC_FORM_SUBMISSIONS, fid)

    # ── Leads ────────────────────────────────────────────────
    async def list_leads(self, org_id, status=None, limit=20, offset=0):
        if status:
            return self._many(
                await self.find_all(
                    Q.LIST_LEADS_BY_STATUS, org_id, status, limit, offset
                ),
                Lead,
            )
        return self._many(
            await self.find_all(Q.LIST_LEADS, org_id, limit, offset), Lead
        )

    async def get_lead(self, lid):
        return self._one(Lead, await self.find_one(Q.GET_LEAD, lid))

    async def get_lead_by_email(self, org_id, email):
        return self._one(Lead, await self.find_one(Q.GET_LEAD_BY_EMAIL, org_id, email))

    async def create_lead(
        self,
        lid,
        org_id,
        email,
        first_name,
        last_name,
        company,
        job_title,
        phone,
        source,
        source_detail,
        utm_source,
        utm_medium,
        utm_campaign,
        utm_term,
        utm_content,
        referrer_url,
        landing_page,
        capture_form_id,
        custom_fields,
        consent_email,
        consent_tracking,
        consent_at,
        ip_address,
        user_agent,
    ):
        await self.execute(
            Q.INSERT_LEAD,
            lid,
            org_id,
            email,
            first_name,
            last_name,
            company,
            job_title,
            phone,
            source,
            source_detail,
            utm_source,
            utm_medium,
            utm_campaign,
            utm_term,
            utm_content,
            referrer_url,
            landing_page,
            capture_form_id,
            json.dumps(custom_fields),
            int(consent_email),
            int(consent_tracking),
            consent_at,
            ip_address,
            user_agent,
        )

    async def update_lead(
        self, lid, first_name, last_name, company, job_title, status, custom_fields
    ):
        await self.execute(
            Q.UPDATE_LEAD,
            first_name,
            last_name,
            company,
            job_title,
            status,
            json.dumps(custom_fields),
            lid,
        )

    async def update_lead_score(self, lid, delta):
        await self.execute(Q.UPDATE_LEAD_SCORE, delta, lid)

    async def delete_lead(self, lid):
        await self.execute(Q.DELETE_LEAD, lid)

    # ── Lead Tags ────────────────────────────────────────────
    async def list_lead_tags(self, org_id, lead_id):
        rows = await self.find_all(Q.LIST_LEAD_TAGS, org_id, lead_id)
        return [r["tag"] for r in rows]

    async def add_lead_tag(self, org_id, lead_id, tag):
        await self.execute(Q.ADD_LEAD_TAG, org_id, lead_id, tag)

    async def remove_lead_tag(self, org_id, lead_id, tag):
        await self.execute(Q.REMOVE_LEAD_TAG, org_id, lead_id, tag)

    # ── Lead Events ──────────────────────────────────────────
    async def list_lead_events(self, lead_id, limit=50, offset=0):
        return self._many(
            await self.find_all(Q.LIST_LEAD_EVENTS, lead_id, limit, offset), LeadEvent
        )

    async def create_lead_event(
        self, eid, lead_id, org_id, event_type, metadata, actor_id
    ):
        await self.execute(
            Q.INSERT_LEAD_EVENT,
            eid,
            lead_id,
            org_id,
            event_type,
            json.dumps(metadata),
            actor_id,
        )

    # ── Lead Score Rules ─────────────────────────────────────
    async def list_score_rules(self, org_id):
        return self._many(
            await self.find_all(Q.LIST_SCORE_RULES, org_id), LeadScoreRule
        )

    async def get_score_rule(self, rid):
        return self._one(LeadScoreRule, await self.find_one(Q.GET_SCORE_RULE, rid))

    async def create_score_rule(
        self, rid, org_id, name, trigger_event, condition, score_delta, is_active
    ):
        await self.execute(
            Q.INSERT_SCORE_RULE,
            rid,
            org_id,
            name,
            trigger_event,
            json.dumps(condition),
            score_delta,
            int(is_active),
        )

    async def update_score_rule(
        self, rid, name, trigger_event, condition, score_delta, is_active
    ):
        await self.execute(
            Q.UPDATE_SCORE_RULE,
            name,
            trigger_event,
            json.dumps(condition),
            score_delta,
            int(is_active),
            rid,
        )

    async def delete_score_rule(self, rid):
        await self.execute(Q.DELETE_SCORE_RULE, rid)

    # ── Lead Pipelines ───────────────────────────────────────
    async def list_pipelines(self, org_id):
        return self._many(await self.find_all(Q.LIST_PIPELINES, org_id), LeadPipeline)

    async def get_pipeline(self, pid):
        return self._one(LeadPipeline, await self.find_one(Q.GET_PIPELINE, pid))

    async def create_pipeline(self, pid, org_id, name, description, sort_order):
        await self.execute(
            Q.INSERT_PIPELINE, pid, org_id, name, description, sort_order
        )

    async def update_pipeline(self, pid, name, description, sort_order):
        await self.execute(Q.UPDATE_PIPELINE, name, description, sort_order, pid)

    async def delete_pipeline(self, pid):
        await self.execute(Q.DELETE_PIPELINE, pid)

    # ── Pipeline Stages ──────────────────────────────────────
    async def list_stages(self, pipeline_id):
        return self._many(
            await self.find_all(Q.LIST_STAGES, pipeline_id), PipelineStage
        )

    async def get_stage(self, sid):
        return self._one(PipelineStage, await self.find_one(Q.GET_STAGE, sid))

    async def create_stage(self, sid, pipeline_id, name, sort_order, stage_type, color):
        await self.execute(
            Q.INSERT_STAGE, sid, pipeline_id, name, sort_order, stage_type, color
        )

    async def update_stage(self, sid, name, sort_order, stage_type, color):
        await self.execute(Q.UPDATE_STAGE, name, sort_order, stage_type, color, sid)

    async def delete_stage(self, sid):
        await self.execute(Q.DELETE_STAGE, sid)

    # ── Lead Pipeline Entries ────────────────────────────────
    async def list_pipeline_entries(self, pipeline_id, limit=50, offset=0):
        return self._many(
            await self.find_all(Q.LIST_PIPELINE_ENTRIES, pipeline_id, limit, offset),
            LeadPipelineEntry,
        )

    async def get_pipeline_entry(self, eid):
        return self._one(
            LeadPipelineEntry, await self.find_one(Q.GET_PIPELINE_ENTRY, eid)
        )

    async def create_pipeline_entry(
        self, eid, lead_id, pipeline_id, stage_id, assigned_to, deal_value, notes
    ):
        await self.execute(
            Q.INSERT_PIPELINE_ENTRY,
            eid,
            lead_id,
            pipeline_id,
            stage_id,
            assigned_to,
            deal_value,
            notes,
        )

    async def update_pipeline_entry(
        self, eid, stage_id, assigned_to, deal_value, notes
    ):
        await self.execute(
            Q.UPDATE_PIPELINE_ENTRY, stage_id, assigned_to, deal_value, notes, eid
        )

    async def delete_pipeline_entry(self, eid):
        await self.execute(Q.DELETE_PIPELINE_ENTRY, eid)

    # ── Email Sequences ──────────────────────────────────────
    async def list_sequences(self, org_id):
        return self._many(await self.find_all(Q.LIST_SEQUENCES, org_id), EmailSequence)

    async def get_sequence(self, sid):
        return self._one(EmailSequence, await self.find_one(Q.GET_SEQUENCE, sid))

    async def create_sequence(
        self, sid, org_id, name, description, trigger_type, created_by
    ):
        await self.execute(
            Q.INSERT_SEQUENCE, sid, org_id, name, description, trigger_type, created_by
        )

    async def update_sequence(self, sid, name, description, trigger_type, status):
        await self.execute(
            Q.UPDATE_SEQUENCE, name, description, trigger_type, status, sid
        )

    async def delete_sequence(self, sid):
        await self.execute(Q.DELETE_SEQUENCE, sid)

    # ── Email Sequence Steps ─────────────────────────────────
    async def list_steps(self, sequence_id):
        return self._many(
            await self.find_all(Q.LIST_STEPS, sequence_id), EmailSequenceStep
        )

    async def get_step(self, step_id):
        return self._one(EmailSequenceStep, await self.find_one(Q.GET_STEP, step_id))

    async def create_step(
        self,
        step_id,
        sequence_id,
        step_number,
        delay_days,
        subject,
        body_html,
        body_text,
    ):
        await self.execute(
            Q.INSERT_STEP,
            step_id,
            sequence_id,
            step_number,
            delay_days,
            subject,
            body_html,
            body_text,
        )

    async def update_step(self, step_id, delay_days, subject, body_html, body_text):
        await self.execute(
            Q.UPDATE_STEP, delay_days, subject, body_html, body_text, step_id
        )

    async def delete_step(self, step_id):
        await self.execute(Q.DELETE_STEP, step_id)

    # ── Lead Sequence Enrollments ────────────────────────────
    async def list_enrollments(self, sequence_id, limit=50, offset=0):
        return self._many(
            await self.find_all(Q.LIST_ENROLLMENTS, sequence_id, limit, offset),
            LeadSequenceEnrollment,
        )

    async def get_enrollment(self, eid):
        return self._one(
            LeadSequenceEnrollment, await self.find_one(Q.GET_ENROLLMENT, eid)
        )

    async def create_enrollment(self, eid, lead_id, sequence_id):
        await self.execute(Q.INSERT_ENROLLMENT, eid, lead_id, sequence_id)

    async def update_enrollment(self, eid, current_step, status):
        await self.execute(Q.UPDATE_ENROLLMENT, current_step, status, eid)
