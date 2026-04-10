"""Phase 5 Step 24 — Marketing service."""

from api.marketing.repository import MarketingRepository
from utils.helpers import new_id, paginate


class MarketingService:
    def __init__(self, env, ctx=None):
        self._repo = MarketingRepository(env.DB, ctx)

    # ── Distribution Channels ────────────────────────────────
    async def list_channels(self, org_id):
        items = await self._repo.list_channels(org_id)
        return [c.to_dict() for c in items]

    async def get_channel(self, cid):
        c = await self._repo.get_channel(cid)
        if not c:
            raise ValueError("Channel not found")
        return c.to_dict(scope="admin")

    async def create_channel(
        self, org_id, name, channel_type, config=None, kv_secret_key="", created_by=""
    ):
        cid = new_id()
        await self._repo.create_channel(
            cid,
            org_id,
            name,
            channel_type,
            config or {},
            kv_secret_key,
            True,
            created_by,
        )
        return {"id": cid}

    async def update_channel(
        self, cid, name=None, channel_type=None, config=None, is_active=None
    ):
        existing = await self._repo.get_channel(cid)
        if not existing:
            raise ValueError("Channel not found")
        await self._repo.update_channel(
            cid,
            name or existing.name,
            channel_type or existing.channel_type,
            config if config is not None else existing.config,
            is_active if is_active is not None else existing.is_active,
        )
        return {"id": cid}

    async def delete_channel(self, cid):
        existing = await self._repo.get_channel(cid)
        if not existing:
            raise ValueError("Channel not found")
        await self._repo.delete_channel(cid)

    # ── Scheduled Publications ───────────────────────────────
    async def list_scheduled(self, user_id):
        items = await self._repo.list_scheduled(user_id)
        return [s.to_dict() for s in items]

    async def get_scheduled(self, sid):
        s = await self._repo.get_scheduled(sid)
        if not s:
            raise ValueError("Scheduled publication not found")
        return s.to_dict()

    async def create_scheduled(
        self, article_id, scheduled_by, scheduled_at, timezone="UTC"
    ):
        sid = new_id()
        await self._repo.create_scheduled(
            sid, article_id, scheduled_by, scheduled_at, timezone
        )
        return {"id": sid}

    async def update_scheduled_status(
        self, sid, status, published_at="", error_message=""
    ):
        existing = await self._repo.get_scheduled(sid)
        if not existing:
            raise ValueError("Scheduled publication not found")
        await self._repo.update_scheduled_status(
            sid, status, published_at, error_message
        )
        return {"id": sid}

    async def delete_scheduled(self, sid):
        existing = await self._repo.get_scheduled(sid)
        if not existing:
            raise ValueError("Scheduled publication not found")
        await self._repo.delete_scheduled(sid)

    # ── Content Distribution Jobs ────────────────────────────
    async def list_dist_jobs(self, org_id, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_dist_jobs(org_id, lim, off)
        return {"jobs": [j.to_dict() for j in items], "page": page, "limit": lim}

    async def get_dist_job(self, jid):
        j = await self._repo.get_dist_job(jid)
        if not j:
            raise ValueError("Distribution job not found")
        return j.to_dict()

    async def create_dist_job(
        self, org_id, article_id, channel_id, distribute_at, run_id=""
    ):
        jid = new_id()
        await self._repo.create_dist_job(
            jid, org_id, article_id, channel_id, distribute_at, run_id
        )
        return {"id": jid}

    async def update_dist_job_status(
        self, jid, status, external_id="", external_url="", error_message=""
    ):
        existing = await self._repo.get_dist_job(jid)
        if not existing:
            raise ValueError("Distribution job not found")
        await self._repo.update_dist_job_status(
            jid, status, external_id, external_url, error_message
        )
        return {"id": jid}

    # ── Content Syndication ──────────────────────────────────
    async def list_syndications(self, article_id):
        items = await self._repo.list_syndications(article_id)
        return [s.to_dict() for s in items]

    async def create_syndication(
        self, article_id, platform, external_url, canonical_back_link=True
    ):
        sid = new_id()
        await self._repo.create_syndication(
            sid, article_id, platform, external_url, canonical_back_link
        )
        return {"id": sid}

    async def delete_syndication(self, sid):
        await self._repo.delete_syndication(sid)

    # ── RSS Feeds ────────────────────────────────────────────
    async def list_rss_feeds(self, org_id):
        items = await self._repo.list_rss_feeds(org_id)
        return [f.to_dict() for f in items]

    async def get_rss_feed(self, fid):
        f = await self._repo.get_rss_feed(fid)
        if not f:
            raise ValueError("RSS feed not found")
        return f.to_dict()

    async def create_rss_feed(
        self,
        org_id,
        name,
        slug,
        description="",
        filter_tags=None,
        filter_authors=None,
        max_items=50,
        include_premium=False,
        is_active=True,
    ):
        fid = new_id()
        await self._repo.create_rss_feed(
            fid,
            org_id,
            name,
            slug,
            description,
            filter_tags or [],
            filter_authors or [],
            max_items,
            include_premium,
            is_active,
        )
        return {"id": fid}

    async def update_rss_feed(
        self,
        fid,
        name=None,
        description=None,
        filter_tags=None,
        filter_authors=None,
        max_items=None,
        include_premium=None,
        is_active=None,
    ):
        existing = await self._repo.get_rss_feed(fid)
        if not existing:
            raise ValueError("RSS feed not found")
        await self._repo.update_rss_feed(
            fid,
            name or existing.name,
            description if description is not None else existing.description,
            filter_tags if filter_tags is not None else existing.filter_tags,
            filter_authors if filter_authors is not None else existing.filter_authors,
            max_items if max_items is not None else existing.max_items,
            include_premium
            if include_premium is not None
            else existing.include_premium,
            is_active if is_active is not None else existing.is_active,
        )
        return {"id": fid}

    async def delete_rss_feed(self, fid):
        existing = await self._repo.get_rss_feed(fid)
        if not existing:
            raise ValueError("RSS feed not found")
        await self._repo.delete_rss_feed(fid)

    # ── Content Repurposing ──────────────────────────────────
    async def list_repurposing(self, org_id, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_repurposing(org_id, lim, off)
        return {"jobs": [j.to_dict() for j in items], "page": page, "limit": lim}

    async def get_repurposing(self, rid):
        r = await self._repo.get_repurposing(rid)
        if not r:
            raise ValueError("Repurposing job not found")
        return r.to_dict()

    async def create_repurposing(
        self, org_id, article_id, fmt, input_options=None, created_by=""
    ):
        rid = new_id()
        await self._repo.create_repurposing(
            rid,
            org_id,
            article_id,
            fmt,
            input_options or {},
            created_by,
        )
        return {"id": rid}

    async def update_repurposing_status(self, rid, status, output_content=""):
        existing = await self._repo.get_repurposing(rid)
        if not existing:
            raise ValueError("Repurposing job not found")
        await self._repo.update_repurposing_status(rid, status, output_content)
        return {"id": rid}

    # ── Campaigns ────────────────────────────────────────────
    async def list_campaigns(self, org_id, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_campaigns(org_id, lim, off)
        return {"campaigns": [c.to_dict() for c in items], "page": page, "limit": lim}

    async def get_campaign(self, cid):
        c = await self._repo.get_campaign(cid)
        if not c:
            raise ValueError("Campaign not found")
        return c.to_dict()

    async def create_campaign(
        self,
        org_id,
        name,
        description="",
        ctype="content",
        start_date="",
        end_date="",
        budget_cents=0,
        goal_id="",
        created_by="",
    ):
        cid = new_id()
        await self._repo.create_campaign(
            cid,
            org_id,
            name,
            description,
            ctype,
            start_date,
            end_date,
            budget_cents,
            goal_id,
            created_by,
        )
        return {"id": cid}

    async def update_campaign(
        self,
        cid,
        name=None,
        description=None,
        status=None,
        start_date=None,
        end_date=None,
        budget_cents=None,
    ):
        existing = await self._repo.get_campaign(cid)
        if not existing:
            raise ValueError("Campaign not found")
        await self._repo.update_campaign(
            cid,
            name or existing.name,
            description if description is not None else existing.description,
            status or existing.status,
            start_date if start_date is not None else existing.start_date,
            end_date if end_date is not None else existing.end_date,
            budget_cents if budget_cents is not None else existing.budget_cents,
        )
        return {"id": cid}

    async def delete_campaign(self, cid):
        existing = await self._repo.get_campaign(cid)
        if not existing:
            raise ValueError("Campaign not found")
        await self._repo.delete_campaign(cid)

    # ── Campaign Articles ────────────────────────────────────
    async def list_campaign_articles(self, campaign_id):
        return await self._repo.list_campaign_articles(campaign_id)

    async def add_campaign_article(self, campaign_id, article_id):
        await self._repo.add_campaign_article(campaign_id, article_id)

    async def remove_campaign_article(self, campaign_id, article_id):
        await self._repo.remove_campaign_article(campaign_id, article_id)
