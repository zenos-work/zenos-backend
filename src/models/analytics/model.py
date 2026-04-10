"""Phase 6 Step 26 — Analytics-engine models."""

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
class AnalyticsEvent:
    id: str = ""
    org_id: str = ""
    user_id: str = ""
    session_id: str = ""
    anonymous_id: str = ""
    event_category: str = ""
    event_action: str = ""
    event_label: str = ""
    event_value: int = 0
    resource_type: str = ""
    resource_id: str = ""
    page_url: str = ""
    referrer_url: str = ""
    utm_source: str = ""
    utm_medium: str = ""
    utm_campaign: str = ""
    properties: dict = field(default_factory=dict)
    device_type: str = ""
    country_code: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id", ""),
            user_id=row.get("user_id", "") or "",
            session_id=row.get("session_id", "") or "",
            anonymous_id=row.get("anonymous_id", "") or "",
            event_category=row.get("event_category", ""),
            event_action=row.get("event_action", ""),
            event_label=row.get("event_label", "") or "",
            event_value=int(row.get("event_value", 0)),
            resource_type=row.get("resource_type", "") or "",
            resource_id=row.get("resource_id", "") or "",
            page_url=row.get("page_url", "") or "",
            referrer_url=row.get("referrer_url", "") or "",
            utm_source=row.get("utm_source", "") or "",
            utm_medium=row.get("utm_medium", "") or "",
            utm_campaign=row.get("utm_campaign", "") or "",
            properties=_json_field(row, "properties"),
            device_type=row.get("device_type", "") or "",
            country_code=row.get("country_code", "") or "",
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, **_):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "anonymous_id": self.anonymous_id,
            "event_category": self.event_category,
            "event_action": self.event_action,
            "event_label": self.event_label,
            "event_value": self.event_value,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "page_url": self.page_url,
            "referrer_url": self.referrer_url,
            "utm_source": self.utm_source,
            "utm_medium": self.utm_medium,
            "utm_campaign": self.utm_campaign,
            "properties": self.properties,
            "device_type": self.device_type,
            "country_code": self.country_code,
            "created_at": self.created_at,
        }


@dataclass
class ConversionGoal:
    id: str = ""
    org_id: str = ""
    name: str = ""
    goal_type: str = ""
    target_event_category: str = ""
    target_event_action: str = ""
    target_resource_id: str = ""
    value_cents: int = 0
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
            goal_type=row.get("goal_type", ""),
            target_event_category=row.get("target_event_category", "") or "",
            target_event_action=row.get("target_event_action", "") or "",
            target_resource_id=row.get("target_resource_id", "") or "",
            value_cents=int(row.get("value_cents", 0)),
            is_active=bool(row.get("is_active", 1)),
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, **_):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "goal_type": self.goal_type,
            "target_event_category": self.target_event_category,
            "target_event_action": self.target_event_action,
            "target_resource_id": self.target_resource_id,
            "value_cents": self.value_cents,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


@dataclass
class ConversionEvent:
    id: str = ""
    goal_id: str = ""
    org_id: str = ""
    user_id: str = ""
    anonymous_id: str = ""
    session_id: str = ""
    event_id: str = ""
    value_cents: int = 0
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            goal_id=row.get("goal_id", ""),
            org_id=row.get("org_id", ""),
            user_id=row.get("user_id", "") or "",
            anonymous_id=row.get("anonymous_id", "") or "",
            session_id=row.get("session_id", "") or "",
            event_id=row.get("event_id", "") or "",
            value_cents=int(row.get("value_cents", 0)),
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, **_):
        return {
            "id": self.id,
            "goal_id": self.goal_id,
            "org_id": self.org_id,
            "user_id": self.user_id,
            "anonymous_id": self.anonymous_id,
            "session_id": self.session_id,
            "event_id": self.event_id,
            "value_cents": self.value_cents,
            "created_at": self.created_at,
        }


@dataclass
class FunnelDefinition:
    id: str = ""
    org_id: str = ""
    name: str = ""
    description: str = ""
    is_active: bool = True
    created_by: str = ""
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
            is_active=bool(row.get("is_active", 1)),
            created_by=row.get("created_by", ""),
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, **_):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at,
        }


@dataclass
class FunnelStep:
    id: str = ""
    funnel_id: str = ""
    step_number: int = 0
    name: str = ""
    event_category: str = ""
    event_action: str = ""
    resource_type: str = ""
    resource_id: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            funnel_id=row.get("funnel_id", ""),
            step_number=int(row.get("step_number", 0)),
            name=row.get("name", ""),
            event_category=row.get("event_category", ""),
            event_action=row.get("event_action", ""),
            resource_type=row.get("resource_type", "") or "",
            resource_id=row.get("resource_id", "") or "",
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, **_):
        return {
            "id": self.id,
            "funnel_id": self.funnel_id,
            "step_number": self.step_number,
            "name": self.name,
            "event_category": self.event_category,
            "event_action": self.event_action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "created_at": self.created_at,
        }


@dataclass
class AbExperiment:
    id: str = ""
    org_id: str = ""
    name: str = ""
    hypothesis: str = ""
    status: str = "draft"
    traffic_split: dict = field(default_factory=dict)
    success_goal_id: str = ""
    started_at: str = ""
    ended_at: str = ""
    winner_variant: str = ""
    created_by: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id", ""),
            name=row.get("name", ""),
            hypothesis=row.get("hypothesis", "") or "",
            status=row.get("status", "draft"),
            traffic_split=_json_field(row, "traffic_split"),
            success_goal_id=row.get("success_goal_id", "") or "",
            started_at=row.get("started_at", "") or "",
            ended_at=row.get("ended_at", "") or "",
            winner_variant=row.get("winner_variant", "") or "",
            created_by=row.get("created_by", ""),
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, **_):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "hypothesis": self.hypothesis,
            "status": self.status,
            "traffic_split": self.traffic_split,
            "success_goal_id": self.success_goal_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "winner_variant": self.winner_variant,
            "created_by": self.created_by,
            "created_at": self.created_at,
        }


@dataclass
class AbExperimentVariant:
    id: str = ""
    experiment_id: str = ""
    name: str = ""
    description: str = ""
    changes: dict = field(default_factory=dict)
    impressions: int = 0
    conversions: int = 0
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            experiment_id=row.get("experiment_id", ""),
            name=row.get("name", ""),
            description=row.get("description", "") or "",
            changes=_json_field(row, "changes"),
            impressions=int(row.get("impressions", 0)),
            conversions=int(row.get("conversions", 0)),
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, **_):
        return {
            "id": self.id,
            "experiment_id": self.experiment_id,
            "name": self.name,
            "description": self.description,
            "changes": self.changes,
            "impressions": self.impressions,
            "conversions": self.conversions,
            "created_at": self.created_at,
        }
