"""Phase 5 Step 25 — Lead-generation models."""

import json
from dataclasses import dataclass, field


def _json_field(row, key, default=None):
    v = row.get(key)
    if v is None:
        return default if default is not None else {}
    if isinstance(v, (dict, list)):
        return v
    try:
        return json.loads(v)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else {}


@dataclass
class LeadCaptureForm:
    id: str = ""
    org_id: str = ""
    owner_id: str = ""
    name: str = ""
    slug: str = ""
    description: str = ""
    placement: str = "inline"
    fields_schema: dict = field(default_factory=dict)
    submit_button_text: str = "Subscribe"
    success_message: str = ""
    redirect_url: str = ""
    tags_on_submit: list = field(default_factory=list)
    workflow_id: str = ""
    is_active: bool = True
    submission_count: int = 0
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id", ""),
            owner_id=row.get("owner_id", ""),
            name=row.get("name", ""),
            slug=row.get("slug", ""),
            description=row.get("description", "") or "",
            placement=row.get("placement", "inline"),
            fields_schema=_json_field(row, "fields_schema"),
            submit_button_text=row.get("submit_button_text", "Subscribe"),
            success_message=row.get("success_message", "") or "",
            redirect_url=row.get("redirect_url", "") or "",
            tags_on_submit=_json_field(row, "tags_on_submit", []),
            workflow_id=row.get("workflow_id", "") or "",
            is_active=bool(row.get("is_active", 1)),
            submission_count=int(row.get("submission_count", 0)),
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", ""),
        )

    def to_dict(self, **_):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "owner_id": self.owner_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "placement": self.placement,
            "fields_schema": self.fields_schema,
            "submit_button_text": self.submit_button_text,
            "success_message": self.success_message,
            "redirect_url": self.redirect_url,
            "tags_on_submit": self.tags_on_submit,
            "workflow_id": self.workflow_id,
            "is_active": self.is_active,
            "submission_count": self.submission_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Lead:
    id: str = ""
    org_id: str = ""
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    company: str = ""
    job_title: str = ""
    phone: str = ""
    source: str = ""
    source_detail: str = ""
    utm_source: str = ""
    utm_medium: str = ""
    utm_campaign: str = ""
    utm_term: str = ""
    utm_content: str = ""
    referrer_url: str = ""
    landing_page: str = ""
    capture_form_id: str = ""
    custom_fields: dict = field(default_factory=dict)
    score: int = 0
    status: str = "new"
    consent_email: bool = False
    consent_tracking: bool = False
    consent_at: str = ""
    ip_address: str = ""
    user_agent: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id", ""),
            email=row.get("email", ""),
            first_name=row.get("first_name", "") or "",
            last_name=row.get("last_name", "") or "",
            company=row.get("company", "") or "",
            job_title=row.get("job_title", "") or "",
            phone=row.get("phone", "") or "",
            source=row.get("source", "") or "",
            source_detail=row.get("source_detail", "") or "",
            utm_source=row.get("utm_source", "") or "",
            utm_medium=row.get("utm_medium", "") or "",
            utm_campaign=row.get("utm_campaign", "") or "",
            utm_term=row.get("utm_term", "") or "",
            utm_content=row.get("utm_content", "") or "",
            referrer_url=row.get("referrer_url", "") or "",
            landing_page=row.get("landing_page", "") or "",
            capture_form_id=row.get("capture_form_id", "") or "",
            custom_fields=_json_field(row, "custom_fields"),
            score=int(row.get("score", 0)),
            status=row.get("status", "new"),
            consent_email=bool(row.get("consent_email", 0)),
            consent_tracking=bool(row.get("consent_tracking", 0)),
            consent_at=row.get("consent_at", "") or "",
            ip_address=row.get("ip_address", "") or "",
            user_agent=row.get("user_agent", "") or "",
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", ""),
        )

    def to_dict(self, scope="public"):
        d = {
            "id": self.id,
            "org_id": self.org_id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "company": self.company,
            "job_title": self.job_title,
            "source": self.source,
            "score": self.score,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if scope == "admin":
            d.update(
                {
                    "phone": self.phone,
                    "source_detail": self.source_detail,
                    "utm_source": self.utm_source,
                    "utm_medium": self.utm_medium,
                    "utm_campaign": self.utm_campaign,
                    "referrer_url": self.referrer_url,
                    "landing_page": self.landing_page,
                    "capture_form_id": self.capture_form_id,
                    "custom_fields": self.custom_fields,
                    "consent_email": self.consent_email,
                    "consent_tracking": self.consent_tracking,
                    "ip_address": self.ip_address,
                }
            )
        return d


@dataclass
class LeadEvent:
    id: str = ""
    lead_id: str = ""
    org_id: str = ""
    event_type: str = ""
    metadata: dict = field(default_factory=dict)
    actor_id: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            lead_id=row.get("lead_id", ""),
            org_id=row.get("org_id", ""),
            event_type=row.get("event_type", ""),
            metadata=_json_field(row, "metadata"),
            actor_id=row.get("actor_id", "") or "",
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, **_):
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "org_id": self.org_id,
            "event_type": self.event_type,
            "metadata": self.metadata,
            "actor_id": self.actor_id,
            "created_at": self.created_at,
        }


@dataclass
class LeadScoreRule:
    id: str = ""
    org_id: str = ""
    name: str = ""
    trigger_event: str = ""
    condition: dict = field(default_factory=dict)
    score_delta: int = 0
    is_active: bool = True
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id", ""),
            name=row.get("name", ""),
            trigger_event=row.get("trigger_event", ""),
            condition=_json_field(row, "condition"),
            score_delta=int(row.get("score_delta", 0)),
            is_active=bool(row.get("is_active", 1)),
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, **_):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "trigger_event": self.trigger_event,
            "condition": self.condition,
            "score_delta": self.score_delta,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


@dataclass
class LeadPipeline:
    id: str = ""
    org_id: str = ""
    name: str = ""
    description: str = ""
    sort_order: int = 0
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id", ""),
            name=row.get("name", ""),
            description=row.get("description", "") or "",
            sort_order=int(row.get("sort_order", 0)),
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, **_):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "description": self.description,
            "sort_order": self.sort_order,
            "created_at": self.created_at,
        }


@dataclass
class PipelineStage:
    id: str = ""
    pipeline_id: str = ""
    name: str = ""
    sort_order: int = 0
    stage_type: str = "open"
    color: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            pipeline_id=row.get("pipeline_id", ""),
            name=row.get("name", ""),
            sort_order=int(row.get("sort_order", 0)),
            stage_type=row.get("stage_type", "open"),
            color=row.get("color", "") or "",
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, **_):
        return {
            "id": self.id,
            "pipeline_id": self.pipeline_id,
            "name": self.name,
            "sort_order": self.sort_order,
            "stage_type": self.stage_type,
            "color": self.color,
            "created_at": self.created_at,
        }


@dataclass
class LeadPipelineEntry:
    id: str = ""
    lead_id: str = ""
    pipeline_id: str = ""
    stage_id: str = ""
    assigned_to: str = ""
    deal_value: int = 0
    notes: str = ""
    entered_stage_at: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            lead_id=row.get("lead_id", ""),
            pipeline_id=row.get("pipeline_id", ""),
            stage_id=row.get("stage_id", ""),
            assigned_to=row.get("assigned_to", "") or "",
            deal_value=int(row.get("deal_value", 0)),
            notes=row.get("notes", "") or "",
            entered_stage_at=row.get("entered_stage_at", "") or "",
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", ""),
        )

    def to_dict(self, **_):
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "pipeline_id": self.pipeline_id,
            "stage_id": self.stage_id,
            "assigned_to": self.assigned_to,
            "deal_value": self.deal_value,
            "notes": self.notes,
            "entered_stage_at": self.entered_stage_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class EmailSequence:
    id: str = ""
    org_id: str = ""
    name: str = ""
    description: str = ""
    trigger_type: str = ""
    status: str = "draft"
    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id", ""),
            name=row.get("name", ""),
            description=row.get("description", "") or "",
            trigger_type=row.get("trigger_type", ""),
            status=row.get("status", "draft"),
            created_by=row.get("created_by", ""),
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", ""),
        )

    def to_dict(self, **_):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "description": self.description,
            "trigger_type": self.trigger_type,
            "status": self.status,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class EmailSequenceStep:
    id: str = ""
    sequence_id: str = ""
    step_number: int = 0
    delay_days: int = 0
    subject: str = ""
    body_html: str = ""
    body_text: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            sequence_id=row.get("sequence_id", ""),
            step_number=int(row.get("step_number", 0)),
            delay_days=int(row.get("delay_days", 0)),
            subject=row.get("subject", ""),
            body_html=row.get("body_html", "") or "",
            body_text=row.get("body_text", "") or "",
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, **_):
        return {
            "id": self.id,
            "sequence_id": self.sequence_id,
            "step_number": self.step_number,
            "delay_days": self.delay_days,
            "subject": self.subject,
            "body_html": self.body_html,
            "body_text": self.body_text,
            "created_at": self.created_at,
        }


@dataclass
class LeadSequenceEnrollment:
    id: str = ""
    lead_id: str = ""
    sequence_id: str = ""
    current_step: int = 0
    status: str = "active"
    enrolled_at: str = ""
    last_step_at: str = ""
    completed_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            lead_id=row.get("lead_id", ""),
            sequence_id=row.get("sequence_id", ""),
            current_step=int(row.get("current_step", 0)),
            status=row.get("status", "active"),
            enrolled_at=row.get("enrolled_at", "") or "",
            last_step_at=row.get("last_step_at", "") or "",
            completed_at=row.get("completed_at", "") or "",
        )

    def to_dict(self, **_):
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "sequence_id": self.sequence_id,
            "current_step": self.current_step,
            "status": self.status,
            "enrolled_at": self.enrolled_at,
            "last_step_at": self.last_step_at,
            "completed_at": self.completed_at,
        }
