"""Phase 5 Step 24 — Marketing / Content-distribution models."""

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
class DistributionChannel:
    id: str = ""
    org_id: str = ""
    name: str = ""
    channel_type: str = ""
    config: dict = field(default_factory=dict)
    kv_secret_key: str = ""
    is_active: bool = True
    last_used_at: str = ""
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
            channel_type=row.get("channel_type", ""),
            config=_json_field(row, "config"),
            kv_secret_key=row.get("kv_secret_key", ""),
            is_active=bool(row.get("is_active", 1)),
            last_used_at=row.get("last_used_at", "") or "",
            created_by=row.get("created_by", ""),
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", ""),
        )

    def to_dict(self, scope="public"):
        d = {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "channel_type": self.channel_type,
            "is_active": self.is_active,
            "last_used_at": self.last_used_at,
            "created_at": self.created_at,
        }
        if scope == "admin":
            d["config"] = self.config
            d["kv_secret_key"] = self.kv_secret_key
            d["created_by"] = self.created_by
            d["updated_at"] = self.updated_at
        return d


@dataclass
class ScheduledPublication:
    id: str = ""
    article_id: str = ""
    scheduled_by: str = ""
    scheduled_at: str = ""
    timezone: str = "UTC"
    status: str = "pending"
    published_at: str = ""
    error_message: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            article_id=row.get("article_id", ""),
            scheduled_by=row.get("scheduled_by", ""),
            scheduled_at=row.get("scheduled_at", ""),
            timezone=row.get("timezone", "UTC"),
            status=row.get("status", "pending"),
            published_at=row.get("published_at", "") or "",
            error_message=row.get("error_message", "") or "",
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, **_):
        return {
            "id": self.id,
            "article_id": self.article_id,
            "scheduled_by": self.scheduled_by,
            "scheduled_at": self.scheduled_at,
            "timezone": self.timezone,
            "status": self.status,
            "published_at": self.published_at,
            "error_message": self.error_message,
            "created_at": self.created_at,
        }


@dataclass
class ContentDistributionJob:
    id: str = ""
    org_id: str = ""
    article_id: str = ""
    channel_id: str = ""
    distribute_at: str = ""
    status: str = "pending"
    external_id: str = ""
    external_url: str = ""
    error_message: str = ""
    attempt_count: int = 0
    triggered_by_run_id: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id", ""),
            article_id=row.get("article_id", ""),
            channel_id=row.get("channel_id", ""),
            distribute_at=row.get("distribute_at", ""),
            status=row.get("status", "pending"),
            external_id=row.get("external_id", "") or "",
            external_url=row.get("external_url", "") or "",
            error_message=row.get("error_message", "") or "",
            attempt_count=int(row.get("attempt_count", 0)),
            triggered_by_run_id=row.get("triggered_by_run_id", "") or "",
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", ""),
        )

    def to_dict(self, **_):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "article_id": self.article_id,
            "channel_id": self.channel_id,
            "distribute_at": self.distribute_at,
            "status": self.status,
            "external_id": self.external_id,
            "external_url": self.external_url,
            "error_message": self.error_message,
            "attempt_count": self.attempt_count,
            "triggered_by_run_id": self.triggered_by_run_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class ContentSyndication:
    id: str = ""
    article_id: str = ""
    platform: str = ""
    external_url: str = ""
    canonical_back_link: bool = True
    syndicated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            article_id=row.get("article_id", ""),
            platform=row.get("platform", ""),
            external_url=row.get("external_url", ""),
            canonical_back_link=bool(row.get("canonical_back_link", 1)),
            syndicated_at=row.get("syndicated_at", ""),
        )

    def to_dict(self, **_):
        return {
            "id": self.id,
            "article_id": self.article_id,
            "platform": self.platform,
            "external_url": self.external_url,
            "canonical_back_link": self.canonical_back_link,
            "syndicated_at": self.syndicated_at,
        }


@dataclass
class RssFeed:
    id: str = ""
    org_id: str = ""
    name: str = ""
    slug: str = ""
    description: str = ""
    filter_tags: list = field(default_factory=list)
    filter_authors: list = field(default_factory=list)
    max_items: int = 50
    include_premium: bool = False
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
            slug=row.get("slug", ""),
            description=row.get("description", "") or "",
            filter_tags=_json_field(row, "filter_tags", []),
            filter_authors=_json_field(row, "filter_authors", []),
            max_items=int(row.get("max_items", 50)),
            include_premium=bool(row.get("include_premium", 0)),
            is_active=bool(row.get("is_active", 1)),
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, **_):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "filter_tags": self.filter_tags,
            "filter_authors": self.filter_authors,
            "max_items": self.max_items,
            "include_premium": self.include_premium,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


@dataclass
class ContentRepurposingJob:
    id: str = ""
    org_id: str = ""
    article_id: str = ""
    format: str = ""
    status: str = "pending"
    input_options: dict = field(default_factory=dict)
    output_content: str = ""
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
            article_id=row.get("article_id", ""),
            format=row.get("format", ""),
            status=row.get("status", "pending"),
            input_options=_json_field(row, "input_options"),
            output_content=row.get("output_content", "") or "",
            created_by=row.get("created_by", ""),
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", ""),
        )

    def to_dict(self, **_):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "article_id": self.article_id,
            "format": self.format,
            "status": self.status,
            "input_options": self.input_options,
            "output_content": self.output_content,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Campaign:
    id: str = ""
    org_id: str = ""
    name: str = ""
    description: str = ""
    type: str = ""
    status: str = "draft"
    start_date: str = ""
    end_date: str = ""
    budget_cents: int = 0
    goal_id: str = ""
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    revenue_cents: int = 0
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
            type=row.get("type", ""),
            status=row.get("status", "draft"),
            start_date=row.get("start_date", "") or "",
            end_date=row.get("end_date", "") or "",
            budget_cents=int(row.get("budget_cents", 0)),
            goal_id=row.get("goal_id", "") or "",
            impressions=int(row.get("impressions", 0)),
            clicks=int(row.get("clicks", 0)),
            conversions=int(row.get("conversions", 0)),
            revenue_cents=int(row.get("revenue_cents", 0)),
            created_by=row.get("created_by", ""),
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, **_):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "status": self.status,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "budget_cents": self.budget_cents,
            "goal_id": self.goal_id,
            "impressions": self.impressions,
            "clicks": self.clicks,
            "conversions": self.conversions,
            "revenue_cents": self.revenue_cents,
            "created_by": self.created_by,
            "created_at": self.created_at,
        }
