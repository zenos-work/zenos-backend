"""Phase 7 Step 30 — Publication models."""

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
class NewsletterSubscription:
    id: str = ""
    email: str = ""
    status: str = "subscribed"
    source: str = "web"
    confirmed_at: str = ""
    unsubscribed_at: str = ""
    metadata_json: dict = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            email=row.get("email", ""),
            status=row.get("status", "subscribed"),
            source=row.get("source", "web"),
            confirmed_at=row.get("confirmed_at", "") or "",
            unsubscribed_at=row.get("unsubscribed_at", "") or "",
            metadata_json=_json_field(row, "metadata_json"),
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", ""),
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "email": self.email,
            "status": self.status,
            "source": self.source,
            "confirmed_at": self.confirmed_at,
            "unsubscribed_at": self.unsubscribed_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class PublicationIssue:
    id: str = ""
    issue_type: str = "newsletter"
    title: str = ""
    slug: str = ""
    period_start: str = ""
    period_end: str = ""
    status: str = "draft"
    editorial_preface: str = ""
    toc_json: dict = field(default_factory=dict)
    cover_article_id: str = ""
    total_pages: int = 0
    pdf_r2_key: str = ""
    pdf_url: str = ""
    metadata_json: dict = field(default_factory=dict)
    created_by_user_id: str = ""
    approved_by_user_id: str = ""
    approved_at: str = ""
    published_at: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            issue_type=row.get("issue_type", "newsletter"),
            title=row.get("title", ""),
            slug=row.get("slug", ""),
            period_start=row.get("period_start", "") or "",
            period_end=row.get("period_end", "") or "",
            status=row.get("status", "draft"),
            editorial_preface=row.get("editorial_preface", "") or "",
            toc_json=_json_field(row, "toc_json"),
            cover_article_id=row.get("cover_article_id", "") or "",
            total_pages=row.get("total_pages", 0) or 0,
            pdf_r2_key=row.get("pdf_r2_key", "") or "",
            pdf_url=row.get("pdf_url", "") or "",
            metadata_json=_json_field(row, "metadata_json"),
            created_by_user_id=row.get("created_by_user_id", "") or "",
            approved_by_user_id=row.get("approved_by_user_id", "") or "",
            approved_at=row.get("approved_at", "") or "",
            published_at=row.get("published_at", "") or "",
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", ""),
        )

    def to_dict(self, scope="public"):
        d = {
            "id": self.id,
            "issue_type": self.issue_type,
            "title": self.title,
            "slug": self.slug,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "status": self.status,
            "editorial_preface": self.editorial_preface,
            "toc_json": self.toc_json,
            "total_pages": self.total_pages,
            "pdf_url": self.pdf_url,
            "published_at": self.published_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if scope == "admin":
            d["cover_article_id"] = self.cover_article_id
            d["pdf_r2_key"] = self.pdf_r2_key
            d["metadata_json"] = self.metadata_json
            d["created_by_user_id"] = self.created_by_user_id
            d["approved_by_user_id"] = self.approved_by_user_id
            d["approved_at"] = self.approved_at
        return d


@dataclass
class PublicationIssueItem:
    id: str = ""
    issue_id: str = ""
    article_id: str = ""
    section: str = "features"
    position: int = 0
    item_type: str = "article"
    title: str = ""
    excerpt: str = ""
    include_full_content: bool = True
    metadata_json: dict = field(default_factory=dict)
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            issue_id=row.get("issue_id", ""),
            article_id=row.get("article_id", "") or "",
            section=row.get("section", "features"),
            position=row.get("position", 0),
            item_type=row.get("item_type", "article"),
            title=row.get("title", "") or "",
            excerpt=row.get("excerpt", "") or "",
            include_full_content=bool(row.get("include_full_content", 1)),
            metadata_json=_json_field(row, "metadata_json"),
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "issue_id": self.issue_id,
            "article_id": self.article_id,
            "section": self.section,
            "position": self.position,
            "item_type": self.item_type,
            "title": self.title,
            "excerpt": self.excerpt,
            "include_full_content": self.include_full_content,
            "created_at": self.created_at,
        }


@dataclass
class PublicationGenerationRun:
    id: str = ""
    issue_id: str = ""
    job_name: str = ""
    trigger_source: str = "scheduled"
    status: str = "running"
    started_at: str = ""
    finished_at: str = ""
    error_text: str = ""
    metrics_json: dict = field(default_factory=dict)
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            issue_id=row.get("issue_id", "") or "",
            job_name=row.get("job_name", ""),
            trigger_source=row.get("trigger_source", "scheduled"),
            status=row.get("status", "running"),
            started_at=row.get("started_at", ""),
            finished_at=row.get("finished_at", "") or "",
            error_text=row.get("error_text", "") or "",
            metrics_json=_json_field(row, "metrics_json"),
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "issue_id": self.issue_id,
            "job_name": self.job_name,
            "trigger_source": self.trigger_source,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error_text": self.error_text,
            "metrics_json": self.metrics_json,
            "created_at": self.created_at,
        }


@dataclass
class PublicationDelivery:
    id: str = ""
    issue_id: str = ""
    email: str = ""
    channel: str = "email"
    status: str = "queued"
    provider: str = ""
    provider_message_id: str = ""
    error_text: str = ""
    sent_at: str = ""
    last_attempt_at: str = ""
    attempt_count: int = 0
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            issue_id=row.get("issue_id", ""),
            email=row.get("email", ""),
            channel=row.get("channel", "email"),
            status=row.get("status", "queued"),
            provider=row.get("provider", "") or "",
            provider_message_id=row.get("provider_message_id", "") or "",
            error_text=row.get("error_text", "") or "",
            sent_at=row.get("sent_at", "") or "",
            last_attempt_at=row.get("last_attempt_at", "") or "",
            attempt_count=row.get("attempt_count", 0),
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", ""),
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "issue_id": self.issue_id,
            "email": self.email,
            "channel": self.channel,
            "status": self.status,
            "provider": self.provider,
            "sent_at": self.sent_at,
            "attempt_count": self.attempt_count,
            "created_at": self.created_at,
        }
