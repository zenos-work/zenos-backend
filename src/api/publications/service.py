"""Phase 7 Step 30 — Publication service."""

from api.publications.repository import PublicationRepository
from utils.helpers import new_id, paginate


class PublicationService:
    def __init__(self, env, ctx=None):
        self._repo = PublicationRepository(env.DB, ctx)

    # ── Newsletter Subscriptions ─────────────────────────────
    async def list_subscriptions(self, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_subscriptions(lim, off)
        return {
            "subscriptions": [s.to_dict() for s in items],
            "page": page,
            "limit": lim,
        }

    async def get_subscription(self, sid):
        s = await self._repo.get_subscription(sid)
        if not s:
            raise ValueError("Subscription not found")
        return s.to_dict()

    async def create_subscription(self, email, source="web"):
        sid = new_id()
        await self._repo.create_subscription(sid, email, "subscribed", source)
        return {"id": sid}

    async def update_subscription_status(self, sid, status):
        existing = await self._repo.get_subscription(sid)
        if not existing:
            raise ValueError("Subscription not found")
        await self._repo.update_subscription_status(sid, status)
        return {"id": sid}

    async def delete_subscription(self, sid):
        existing = await self._repo.get_subscription(sid)
        if not existing:
            raise ValueError("Subscription not found")
        await self._repo.delete_subscription(sid)

    # ── Publication Issues ───────────────────────────────────
    async def list_issues(self, page=1, limit=20, issue_type=None):
        lim, off = paginate(page, limit)
        if issue_type:
            items = await self._repo.list_issues_by_type(issue_type, lim, off)
        else:
            items = await self._repo.list_issues(lim, off)
        return {"issues": [i.to_dict() for i in items], "page": page, "limit": lim}

    async def get_issue(self, iid):
        i = await self._repo.get_issue(iid)
        if not i:
            raise ValueError("Publication issue not found")
        return i.to_dict(scope="admin")

    async def create_issue(
        self,
        issue_type,
        title,
        slug,
        period_start="",
        period_end="",
        status="draft",
        editorial_preface="",
        toc_json=None,
        cover_article_id="",
        created_by_user_id="",
    ):
        iid = new_id()
        await self._repo.create_issue(
            iid,
            issue_type,
            title,
            slug,
            period_start,
            period_end,
            status,
            editorial_preface,
            toc_json or {},
            cover_article_id,
            created_by_user_id,
        )
        return {"id": iid}

    async def update_issue(self, iid, **kwargs):
        existing = await self._repo.get_issue(iid)
        if not existing:
            raise ValueError("Publication issue not found")
        await self._repo.update_issue(
            iid,
            title=kwargs.get("title") or existing.title,
            editorial_preface=kwargs.get("editorial_preface")
            if kwargs.get("editorial_preface") is not None
            else existing.editorial_preface,
            toc_json=kwargs.get("toc_json")
            if kwargs.get("toc_json") is not None
            else existing.toc_json,
            status=kwargs.get("status") or existing.status,
            total_pages=kwargs.get("total_pages")
            if kwargs.get("total_pages") is not None
            else existing.total_pages,
            pdf_r2_key=kwargs.get("pdf_r2_key")
            if kwargs.get("pdf_r2_key") is not None
            else existing.pdf_r2_key,
            pdf_url=kwargs.get("pdf_url")
            if kwargs.get("pdf_url") is not None
            else existing.pdf_url,
        )
        return {"id": iid}

    async def approve_issue(self, iid, approved_by):
        existing = await self._repo.get_issue(iid)
        if not existing:
            raise ValueError("Publication issue not found")
        await self._repo.approve_issue(iid, approved_by)
        return {"id": iid}

    async def publish_issue(self, iid):
        existing = await self._repo.get_issue(iid)
        if not existing:
            raise ValueError("Publication issue not found")
        await self._repo.publish_issue(iid)
        return {"id": iid}

    async def delete_issue(self, iid):
        existing = await self._repo.get_issue(iid)
        if not existing:
            raise ValueError("Publication issue not found")
        await self._repo.delete_issue(iid)

    # ── Issue Items ──────────────────────────────────────────
    async def list_items(self, issue_id):
        items = await self._repo.list_items(issue_id)
        return [i.to_dict() for i in items]

    async def get_item(self, item_id):
        i = await self._repo.get_item(item_id)
        if not i:
            raise ValueError("Item not found")
        return i.to_dict()

    async def create_item(
        self,
        issue_id,
        article_id="",
        section="features",
        position=0,
        item_type="article",
        title="",
        excerpt="",
        include_full_content=True,
    ):
        item_id = new_id()
        await self._repo.create_item(
            item_id,
            issue_id,
            article_id,
            section,
            position,
            item_type,
            title,
            excerpt,
            include_full_content,
        )
        return {"id": item_id}

    async def update_item(self, item_id, **kwargs):
        existing = await self._repo.get_item(item_id)
        if not existing:
            raise ValueError("Item not found")
        await self._repo.update_item(
            item_id,
            section=kwargs.get("section") or existing.section,
            position=kwargs.get("position")
            if kwargs.get("position") is not None
            else existing.position,
            item_type=kwargs.get("item_type") or existing.item_type,
            title=kwargs.get("title")
            if kwargs.get("title") is not None
            else existing.title,
            excerpt=kwargs.get("excerpt")
            if kwargs.get("excerpt") is not None
            else existing.excerpt,
            include_full_content=kwargs.get("include_full_content")
            if kwargs.get("include_full_content") is not None
            else existing.include_full_content,
        )
        return {"id": item_id}

    async def delete_item(self, item_id):
        existing = await self._repo.get_item(item_id)
        if not existing:
            raise ValueError("Item not found")
        await self._repo.delete_item(item_id)

    # ── Generation Runs ──────────────────────────────────────
    async def list_gen_runs(self, issue_id):
        items = await self._repo.list_gen_runs(issue_id)
        return [r.to_dict() for r in items]

    async def create_gen_run(self, issue_id, job_name, trigger_source="manual"):
        rid = new_id()
        await self._repo.create_gen_run(
            rid, issue_id, job_name, trigger_source, "running"
        )
        return {"id": rid}

    async def update_gen_run(self, rid, status, error_text="", metrics_json=None):
        existing = await self._repo.get_gen_run(rid)
        if not existing:
            raise ValueError("Generation run not found")
        await self._repo.update_gen_run(rid, status, error_text, metrics_json or {})
        return {"id": rid}

    # ── Deliveries ───────────────────────────────────────────
    async def list_deliveries(self, issue_id, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_deliveries(issue_id, lim, off)
        return {"deliveries": [d.to_dict() for d in items], "page": page, "limit": lim}

    async def create_delivery(self, issue_id, email, channel="email"):
        did = new_id()
        await self._repo.create_delivery(did, issue_id, email, channel, "queued")
        return {"id": did}

    async def update_delivery_status(
        self, did, status, provider="", provider_message_id="", error_text=""
    ):
        existing = await self._repo.get_delivery(did)
        if not existing:
            raise ValueError("Delivery not found")
        await self._repo.update_delivery_status(
            did, status, provider, provider_message_id, error_text
        )
        return {"id": did}
