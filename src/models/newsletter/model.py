"""Phase 7 Step 29 — Newsletter models."""

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
class Newsletter:
    id: str = ""
    org_id: str = ""
    owner_id: str = ""
    name: str = ""
    slug: str = ""
    description: str = ""
    logo_url: str = ""
    cover_url: str = ""
    from_name: str = ""
    from_email: str = ""
    reply_to_email: str = ""
    esp_integration_id: str = ""
    is_premium_only: bool = False
    membership_tier: str = ""
    status: str = "active"
    subscriber_count: int = 0
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id", "") or "",
            owner_id=row.get("owner_id", ""),
            name=row.get("name", ""),
            slug=row.get("slug", ""),
            description=row.get("description", "") or "",
            logo_url=row.get("logo_url", "") or "",
            cover_url=row.get("cover_url", "") or "",
            from_name=row.get("from_name", ""),
            from_email=row.get("from_email", ""),
            reply_to_email=row.get("reply_to_email", "") or "",
            esp_integration_id=row.get("esp_integration_id", "") or "",
            is_premium_only=bool(row.get("is_premium_only", 0)),
            membership_tier=row.get("membership_tier", "") or "",
            status=row.get("status", "active"),
            subscriber_count=row.get("subscriber_count", 0),
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", ""),
        )

    def to_dict(self, scope="public"):
        d = {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "logo_url": self.logo_url,
            "cover_url": self.cover_url,
            "from_name": self.from_name,
            "from_email": self.from_email,
            "is_premium_only": self.is_premium_only,
            "status": self.status,
            "subscriber_count": self.subscriber_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if scope == "admin":
            d["owner_id"] = self.owner_id
            d["reply_to_email"] = self.reply_to_email
            d["esp_integration_id"] = self.esp_integration_id
            d["membership_tier"] = self.membership_tier
        return d


@dataclass
class NewsletterSubscriber:
    id: str = ""
    newsletter_id: str = ""
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    lead_id: str = ""
    user_id: str = ""
    status: str = "subscribed"
    consent_at: str = ""
    confirmation_token: str = ""
    confirmed_at: str = ""
    open_count: int = 0
    click_count: int = 0
    last_opened_at: str = ""
    last_clicked_at: str = ""
    subscribed_at: str = ""
    unsubscribed_at: str = ""
    source: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            newsletter_id=row.get("newsletter_id", ""),
            email=row.get("email", ""),
            first_name=row.get("first_name", "") or "",
            last_name=row.get("last_name", "") or "",
            lead_id=row.get("lead_id", "") or "",
            user_id=row.get("user_id", "") or "",
            status=row.get("status", "subscribed"),
            consent_at=row.get("consent_at", "") or "",
            confirmation_token=row.get("confirmation_token", "") or "",
            confirmed_at=row.get("confirmed_at", "") or "",
            open_count=row.get("open_count", 0),
            click_count=row.get("click_count", 0),
            last_opened_at=row.get("last_opened_at", "") or "",
            last_clicked_at=row.get("last_clicked_at", "") or "",
            subscribed_at=row.get("subscribed_at", ""),
            unsubscribed_at=row.get("unsubscribed_at", "") or "",
            source=row.get("source", "") or "",
        )

    def to_dict(self, scope="public"):
        d = {
            "id": self.id,
            "newsletter_id": self.newsletter_id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "status": self.status,
            "open_count": self.open_count,
            "click_count": self.click_count,
            "subscribed_at": self.subscribed_at,
        }
        if scope == "admin":
            d["lead_id"] = self.lead_id
            d["user_id"] = self.user_id
            d["consent_at"] = self.consent_at
            d["confirmed_at"] = self.confirmed_at
            d["last_opened_at"] = self.last_opened_at
            d["last_clicked_at"] = self.last_clicked_at
            d["unsubscribed_at"] = self.unsubscribed_at
            d["source"] = self.source
        return d


@dataclass
class NewsletterIssue:
    id: str = ""
    newsletter_id: str = ""
    subject: str = ""
    preview_text: str = ""
    body_html: str = ""
    body_text: str = ""
    issue_type: str = "digest"
    article_ids: list = field(default_factory=list)
    status: str = "draft"
    scheduled_at: str = ""
    sent_at: str = ""
    send_count: int = 0
    open_count: int = 0
    unique_opens: int = 0
    click_count: int = 0
    unique_clicks: int = 0
    unsub_count: int = 0
    bounce_count: int = 0
    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            newsletter_id=row.get("newsletter_id", ""),
            subject=row.get("subject", ""),
            preview_text=row.get("preview_text", "") or "",
            body_html=row.get("body_html", "") or "",
            body_text=row.get("body_text", "") or "",
            issue_type=row.get("issue_type", "digest"),
            article_ids=_json_field(row, "article_ids", []),
            status=row.get("status", "draft"),
            scheduled_at=row.get("scheduled_at", "") or "",
            sent_at=row.get("sent_at", "") or "",
            send_count=row.get("send_count", 0),
            open_count=row.get("open_count", 0),
            unique_opens=row.get("unique_opens", 0),
            click_count=row.get("click_count", 0),
            unique_clicks=row.get("unique_clicks", 0),
            unsub_count=row.get("unsub_count", 0),
            bounce_count=row.get("bounce_count", 0),
            created_by=row.get("created_by", ""),
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", ""),
        )

    def to_dict(self, scope="public"):
        d = {
            "id": self.id,
            "newsletter_id": self.newsletter_id,
            "subject": self.subject,
            "preview_text": self.preview_text,
            "issue_type": self.issue_type,
            "article_ids": self.article_ids,
            "status": self.status,
            "scheduled_at": self.scheduled_at,
            "sent_at": self.sent_at,
            "send_count": self.send_count,
            "open_count": self.open_count,
            "unique_opens": self.unique_opens,
            "click_count": self.click_count,
            "unique_clicks": self.unique_clicks,
            "unsub_count": self.unsub_count,
            "bounce_count": self.bounce_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if scope == "admin":
            d["body_html"] = self.body_html
            d["body_text"] = self.body_text
            d["created_by"] = self.created_by
        return d


@dataclass
class NewsletterIssueArticle:
    issue_id: str = ""
    article_id: str = ""
    sort_order: int = 0
    blurb: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            issue_id=row.get("issue_id", ""),
            article_id=row.get("article_id", ""),
            sort_order=row.get("sort_order", 0),
            blurb=row.get("blurb", "") or "",
        )

    def to_dict(self, scope="public"):
        return {
            "issue_id": self.issue_id,
            "article_id": self.article_id,
            "sort_order": self.sort_order,
            "blurb": self.blurb,
        }


@dataclass
class NewsletterSendEvent:
    id: str = ""
    issue_id: str = ""
    subscriber_id: str = ""
    event_type: str = ""
    link_url: str = ""
    metadata: dict = field(default_factory=dict)
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            issue_id=row.get("issue_id", ""),
            subscriber_id=row.get("subscriber_id", ""),
            event_type=row.get("event_type", ""),
            link_url=row.get("link_url", "") or "",
            metadata=_json_field(row, "metadata"),
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "issue_id": self.issue_id,
            "subscriber_id": self.subscriber_id,
            "event_type": self.event_type,
            "link_url": self.link_url,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


@dataclass
class NewsletterSegment:
    id: str = ""
    newsletter_id: str = ""
    name: str = ""
    filter_rules: dict = field(default_factory=dict)
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            newsletter_id=row.get("newsletter_id", ""),
            name=row.get("name", ""),
            filter_rules=_json_field(row, "filter_rules"),
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "newsletter_id": self.newsletter_id,
            "name": self.name,
            "filter_rules": self.filter_rules,
            "created_at": self.created_at,
        }
