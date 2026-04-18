"""Phase 5 Step 24 — Marketing repository."""

import json
from db.repository import BaseRepository
from api.marketing import queries as Q
from models.marketing.model import (
    DistributionChannel,
    ScheduledPublication,
    ContentDistributionJob,
    ContentSyndication,
    RssFeed,
    ContentRepurposingJob,
    Campaign,
)


class MarketingRepository(BaseRepository):
    def _one(self, cls, row):
        return self.map_one(row, cls)

    def _many(self, rows, cls):
        return self.map_many(rows, cls)

    # ── Distribution Channels ────────────────────────────────
    async def list_channels(self, org_id):
        return self._many(
            await self.find_all(Q.LIST_CHANNELS, org_id), DistributionChannel
        )

    async def get_channel(self, cid):
        return self._one(DistributionChannel, await self.find_one(Q.GET_CHANNEL, cid))

    async def create_channel(
        self,
        cid,
        org_id,
        name,
        channel_type,
        config,
        kv_secret_key,
        is_active,
        created_by,
    ):
        await self.execute(
            Q.INSERT_CHANNEL,
            cid,
            org_id,
            name,
            channel_type,
            json.dumps(config),
            kv_secret_key,
            int(is_active),
            created_by,
        )

    async def update_channel(self, cid, name, channel_type, config, is_active):
        await self.execute(
            Q.UPDATE_CHANNEL,
            name,
            channel_type,
            json.dumps(config),
            int(is_active),
            cid,
        )

    async def delete_channel(self, cid):
        await self.execute(Q.DELETE_CHANNEL, cid)

    # ── Scheduled Publications ───────────────────────────────
    async def list_scheduled(self, user_id):
        return self._many(
            await self.find_all(Q.LIST_SCHEDULED, user_id), ScheduledPublication
        )

    async def get_scheduled(self, sid):
        return self._one(
            ScheduledPublication, await self.find_one(Q.GET_SCHEDULED, sid)
        )

    async def get_scheduled_by_article(self, article_id):
        return self._one(
            ScheduledPublication,
            await self.find_one(Q.GET_SCHEDULED_BY_ARTICLE, article_id),
        )

    async def create_scheduled(
        self, sid, article_id, scheduled_by, scheduled_at, timezone
    ):
        await self.execute(
            Q.INSERT_SCHEDULED, sid, article_id, scheduled_by, scheduled_at, timezone
        )

    async def update_scheduled_status(
        self, sid, status, published_at="", error_message=""
    ):
        await self.execute(
            Q.UPDATE_SCHEDULED_STATUS, status, published_at, error_message, sid
        )

    async def delete_scheduled(self, sid):
        await self.execute(Q.DELETE_SCHEDULED, sid)

    # ── Content Distribution Jobs ────────────────────────────
    async def list_dist_jobs(self, org_id, limit=20, offset=0):
        return self._many(
            await self.find_all(Q.LIST_DIST_JOBS, org_id, limit, offset),
            ContentDistributionJob,
        )

    async def get_dist_job(self, jid):
        return self._one(
            ContentDistributionJob, await self.find_one(Q.GET_DIST_JOB, jid)
        )

    async def create_dist_job(
        self, jid, org_id, article_id, channel_id, distribute_at, run_id=""
    ):
        await self.execute(
            Q.INSERT_DIST_JOB,
            jid,
            org_id,
            article_id,
            channel_id,
            distribute_at,
            run_id,
        )

    async def update_dist_job_status(
        self, jid, status, external_id="", external_url="", error_message=""
    ):
        await self.execute(
            Q.UPDATE_DIST_JOB_STATUS,
            status,
            external_id,
            external_url,
            error_message,
            jid,
        )

    # ── Content Syndication ──────────────────────────────────
    async def list_syndications(self, article_id):
        return self._many(
            await self.find_all(Q.LIST_SYNDICATIONS, article_id), ContentSyndication
        )

    async def create_syndication(
        self, sid, article_id, platform, external_url, canonical_back_link=True
    ):
        await self.execute(
            Q.INSERT_SYNDICATION,
            sid,
            article_id,
            platform,
            external_url,
            int(canonical_back_link),
        )

    async def delete_syndication(self, sid):
        await self.execute(Q.DELETE_SYNDICATION, sid)

    # ── RSS Feeds ────────────────────────────────────────────
    async def list_rss_feeds(self, org_id):
        return self._many(await self.find_all(Q.LIST_RSS_FEEDS, org_id), RssFeed)

    async def get_rss_feed(self, fid):
        return self._one(RssFeed, await self.find_one(Q.GET_RSS_FEED, fid))

    async def get_rss_feed_by_slug(self, org_id, slug):
        return self._one(
            RssFeed, await self.find_one(Q.GET_RSS_FEED_BY_SLUG, org_id, slug)
        )

    async def create_rss_feed(
        self,
        fid,
        org_id,
        name,
        slug,
        description,
        filter_tags,
        filter_authors,
        max_items,
        include_premium,
        is_active,
    ):
        await self.execute(
            Q.INSERT_RSS_FEED,
            fid,
            org_id,
            name,
            slug,
            description,
            json.dumps(filter_tags),
            json.dumps(filter_authors),
            max_items,
            int(include_premium),
            int(is_active),
        )

    async def update_rss_feed(
        self,
        fid,
        name,
        description,
        filter_tags,
        filter_authors,
        max_items,
        include_premium,
        is_active,
    ):
        await self.execute(
            Q.UPDATE_RSS_FEED,
            name,
            description,
            json.dumps(filter_tags),
            json.dumps(filter_authors),
            max_items,
            int(include_premium),
            int(is_active),
            fid,
        )

    async def delete_rss_feed(self, fid):
        await self.execute(Q.DELETE_RSS_FEED, fid)

    # ── Content Repurposing ──────────────────────────────────
    async def list_repurposing(self, org_id, limit=20, offset=0):
        return self._many(
            await self.find_all(Q.LIST_REPURPOSING, org_id, limit, offset),
            ContentRepurposingJob,
        )

    async def get_repurposing(self, rid):
        return self._one(
            ContentRepurposingJob, await self.find_one(Q.GET_REPURPOSING, rid)
        )

    async def create_repurposing(
        self, rid, org_id, article_id, fmt, input_options, created_by
    ):
        await self.execute(
            Q.INSERT_REPURPOSING,
            rid,
            org_id,
            article_id,
            fmt,
            json.dumps(input_options),
            created_by,
        )

    async def update_repurposing_status(self, rid, status, output_content=""):
        await self.execute(Q.UPDATE_REPURPOSING_STATUS, status, output_content, rid)

    # ── Campaigns ────────────────────────────────────────────
    async def list_campaigns(self, org_id, limit=20, offset=0):
        return self._many(
            await self.find_all(Q.LIST_CAMPAIGNS, org_id, limit, offset), Campaign
        )

    async def get_campaign(self, cid):
        return self._one(Campaign, await self.find_one(Q.GET_CAMPAIGN, cid))

    async def create_campaign(
        self,
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
    ):
        await self.execute(
            Q.INSERT_CAMPAIGN,
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

    async def update_campaign(
        self, cid, name, description, status, start_date, end_date, budget_cents
    ):
        await self.execute(
            Q.UPDATE_CAMPAIGN,
            name,
            description,
            status,
            start_date,
            end_date,
            budget_cents,
            cid,
        )

    async def delete_campaign(self, cid):
        await self.execute(Q.DELETE_CAMPAIGN, cid)

    # ── Campaign Articles ────────────────────────────────────
    async def list_campaign_articles(self, campaign_id):
        rows = await self.find_all(Q.LIST_CAMPAIGN_ARTICLES, campaign_id)
        return [r["article_id"] for r in rows]

    async def add_campaign_article(self, campaign_id, article_id):
        await self.execute(Q.ADD_CAMPAIGN_ARTICLE, campaign_id, article_id)

    async def remove_campaign_article(self, campaign_id, article_id):
        await self.execute(Q.REMOVE_CAMPAIGN_ARTICLE, campaign_id, article_id)
