"""Phase 7 Step 29 — Newsletter service."""

from api.newsletters.repository import NewsletterRepository
from utils.helpers import new_id, paginate


class NewsletterService:
    def __init__(self, env, ctx=None):
        self._repo = NewsletterRepository(env.DB, ctx)

    # ── Newsletters ──────────────────────────────────────────
    async def list_newsletters(self, org_id):
        items = await self._repo.list_newsletters(org_id)
        return [n.to_dict() for n in items]

    async def list_newsletters_by_owner(self, owner_id):
        items = await self._repo.list_newsletters_by_owner(owner_id)
        return [n.to_dict() for n in items]

    async def get_newsletter(self, nid):
        n = await self._repo.get_newsletter(nid)
        if not n:
            raise ValueError("Newsletter not found")
        return n.to_dict(scope="admin")

    async def create_newsletter(
        self,
        org_id,
        owner_id,
        name,
        slug,
        description="",
        logo_url="",
        cover_url="",
        from_name="",
        from_email="",
        reply_to_email="",
        is_premium_only=False,
        membership_tier="",
        status="active",
    ):
        nid = new_id()
        await self._repo.create_newsletter(
            nid,
            org_id,
            owner_id,
            name,
            slug,
            description,
            logo_url,
            cover_url,
            from_name,
            from_email,
            reply_to_email,
            is_premium_only,
            membership_tier,
            status,
        )
        return {"id": nid}

    async def update_newsletter(self, nid, **kwargs):
        existing = await self._repo.get_newsletter(nid)
        if not existing:
            raise ValueError("Newsletter not found")
        await self._repo.update_newsletter(
            nid,
            name=kwargs.get("name") or existing.name,
            description=kwargs.get("description")
            if kwargs.get("description") is not None
            else existing.description,
            logo_url=kwargs.get("logo_url")
            if kwargs.get("logo_url") is not None
            else existing.logo_url,
            cover_url=kwargs.get("cover_url")
            if kwargs.get("cover_url") is not None
            else existing.cover_url,
            from_name=kwargs.get("from_name") or existing.from_name,
            from_email=kwargs.get("from_email") or existing.from_email,
            reply_to_email=kwargs.get("reply_to_email")
            if kwargs.get("reply_to_email") is not None
            else existing.reply_to_email,
            is_premium_only=kwargs.get("is_premium_only")
            if kwargs.get("is_premium_only") is not None
            else existing.is_premium_only,
            membership_tier=kwargs.get("membership_tier")
            if kwargs.get("membership_tier") is not None
            else existing.membership_tier,
            status=kwargs.get("status") or existing.status,
        )
        return {"id": nid}

    async def delete_newsletter(self, nid):
        existing = await self._repo.get_newsletter(nid)
        if not existing:
            raise ValueError("Newsletter not found")
        await self._repo.delete_newsletter(nid)

    # ── Subscribers ──────────────────────────────────────────
    async def list_subscribers(self, newsletter_id, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_subscribers(newsletter_id, lim, off)
        return {"subscribers": [s.to_dict() for s in items], "page": page, "limit": lim}

    async def get_subscriber(self, sid):
        s = await self._repo.get_subscriber(sid)
        if not s:
            raise ValueError("Subscriber not found")
        return s.to_dict(scope="admin")

    async def create_subscriber(
        self,
        newsletter_id,
        email,
        first_name="",
        last_name="",
        source="web",
        status="subscribed",
    ):
        sid = new_id()
        await self._repo.create_subscriber(
            sid, newsletter_id, email, first_name, last_name, source, status
        )
        await self._repo.increment_subscriber_count(newsletter_id)
        return {"id": sid}

    async def update_subscriber_status(self, sid, status):
        existing = await self._repo.get_subscriber(sid)
        if not existing:
            raise ValueError("Subscriber not found")
        await self._repo.update_subscriber_status(sid, status)
        if status == "unsubscribed" and existing.status == "subscribed":
            await self._repo.decrement_subscriber_count(existing.newsletter_id)
        return {"id": sid}

    async def delete_subscriber(self, sid):
        existing = await self._repo.get_subscriber(sid)
        if not existing:
            raise ValueError("Subscriber not found")
        await self._repo.delete_subscriber(sid)
        if existing.status == "subscribed":
            await self._repo.decrement_subscriber_count(existing.newsletter_id)

    # ── Issues ───────────────────────────────────────────────
    async def list_issues(self, newsletter_id, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_issues(newsletter_id, lim, off)
        return {"issues": [i.to_dict() for i in items], "page": page, "limit": lim}

    async def get_issue(self, iid):
        i = await self._repo.get_issue(iid)
        if not i:
            raise ValueError("Issue not found")
        return i.to_dict(scope="admin")

    async def create_issue(
        self,
        newsletter_id,
        subject,
        preview_text="",
        body_html="",
        body_text="",
        issue_type="digest",
        article_ids=None,
        status="draft",
        scheduled_at="",
        created_by="",
    ):
        iid = new_id()
        await self._repo.create_issue(
            iid,
            newsletter_id,
            subject,
            preview_text,
            body_html,
            body_text,
            issue_type,
            article_ids or [],
            status,
            scheduled_at,
            created_by,
        )
        return {"id": iid}

    async def update_issue(self, iid, **kwargs):
        existing = await self._repo.get_issue(iid)
        if not existing:
            raise ValueError("Issue not found")
        await self._repo.update_issue(
            iid,
            subject=kwargs.get("subject") or existing.subject,
            preview_text=kwargs.get("preview_text")
            if kwargs.get("preview_text") is not None
            else existing.preview_text,
            body_html=kwargs.get("body_html")
            if kwargs.get("body_html") is not None
            else existing.body_html,
            body_text=kwargs.get("body_text")
            if kwargs.get("body_text") is not None
            else existing.body_text,
            issue_type=kwargs.get("issue_type") or existing.issue_type,
            article_ids=kwargs.get("article_ids")
            if kwargs.get("article_ids") is not None
            else existing.article_ids,
            status=kwargs.get("status") or existing.status,
            scheduled_at=kwargs.get("scheduled_at")
            if kwargs.get("scheduled_at") is not None
            else existing.scheduled_at,
        )
        return {"id": iid}

    async def update_issue_status(self, iid, status):
        existing = await self._repo.get_issue(iid)
        if not existing:
            raise ValueError("Issue not found")
        await self._repo.update_issue_status(iid, status)
        return {"id": iid}

    async def delete_issue(self, iid):
        existing = await self._repo.get_issue(iid)
        if not existing:
            raise ValueError("Issue not found")
        await self._repo.delete_issue(iid)

    # ── Issue Articles ───────────────────────────────────────
    async def list_issue_articles(self, issue_id):
        items = await self._repo.list_issue_articles(issue_id)
        return [a.to_dict() for a in items]

    async def add_issue_article(self, issue_id, article_id, sort_order=0, blurb=""):
        await self._repo.add_issue_article(issue_id, article_id, sort_order, blurb)

    async def remove_issue_article(self, issue_id, article_id):
        await self._repo.remove_issue_article(issue_id, article_id)

    # ── Send Events ──────────────────────────────────────────
    async def list_send_events(self, issue_id, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_send_events(issue_id, lim, off)
        return {"events": [e.to_dict() for e in items], "page": page, "limit": lim}

    async def create_send_event(
        self, issue_id, subscriber_id, event_type, link_url="", metadata=None
    ):
        eid = new_id()
        await self._repo.create_send_event(
            eid, issue_id, subscriber_id, event_type, link_url, metadata or {}
        )
        return {"id": eid}

    # ── Segments ─────────────────────────────────────────────
    async def list_segments(self, newsletter_id):
        items = await self._repo.list_segments(newsletter_id)
        return [s.to_dict() for s in items]

    async def get_segment(self, sid):
        s = await self._repo.get_segment(sid)
        if not s:
            raise ValueError("Segment not found")
        return s.to_dict()

    async def create_segment(self, newsletter_id, name, filter_rules=None):
        sid = new_id()
        await self._repo.create_segment(sid, newsletter_id, name, filter_rules or {})
        return {"id": sid}

    async def update_segment(self, sid, name=None, filter_rules=None):
        existing = await self._repo.get_segment(sid)
        if not existing:
            raise ValueError("Segment not found")
        await self._repo.update_segment(
            sid,
            name=name or existing.name,
            filter_rules=filter_rules
            if filter_rules is not None
            else existing.filter_rules,
        )
        return {"id": sid}

    async def delete_segment(self, sid):
        existing = await self._repo.get_segment(sid)
        if not existing:
            raise ValueError("Segment not found")
        await self._repo.delete_segment(sid)
