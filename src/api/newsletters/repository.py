"""Phase 7 Step 29 — Newsletter repository."""

import json
from db.repository import BaseRepository
from api.newsletters import queries as Q
from models.newsletter.model import (
    Newsletter,
    NewsletterSubscriber,
    NewsletterIssue,
    NewsletterIssueArticle,
    NewsletterSendEvent,
    NewsletterSegment,
)


class NewsletterRepository(BaseRepository):
    def _one(self, cls, row):
        return self.map_one(row, cls)

    def _many(self, rows, cls):
        return self.map_many(rows, cls)

    # ── Newsletters ──────────────────────────────────────────
    async def list_newsletters(self, org_id):
        return self._many(await self.find_all(Q.LIST_NEWSLETTERS, org_id), Newsletter)

    async def list_newsletters_by_owner(self, owner_id):
        return self._many(
            await self.find_all(Q.LIST_NEWSLETTERS_BY_OWNER, owner_id), Newsletter
        )

    async def get_newsletter(self, nid):
        return self._one(Newsletter, await self.find_one(Q.GET_NEWSLETTER, nid))

    async def create_newsletter(
        self,
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
    ):
        await self.execute(
            Q.INSERT_NEWSLETTER,
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
            int(is_premium_only),
            membership_tier,
            status,
        )

    async def update_newsletter(
        self,
        nid,
        name,
        description,
        logo_url,
        cover_url,
        from_name,
        from_email,
        reply_to_email,
        is_premium_only,
        membership_tier,
        status,
    ):
        await self.execute(
            Q.UPDATE_NEWSLETTER,
            name,
            description,
            logo_url,
            cover_url,
            from_name,
            from_email,
            reply_to_email,
            int(is_premium_only),
            membership_tier,
            status,
            nid,
        )

    async def delete_newsletter(self, nid):
        await self.execute(Q.DELETE_NEWSLETTER, nid)

    async def increment_subscriber_count(self, nid):
        await self.execute(Q.INCREMENT_SUBSCRIBER_COUNT, nid)

    async def decrement_subscriber_count(self, nid):
        await self.execute(Q.DECREMENT_SUBSCRIBER_COUNT, nid)

    # ── Subscribers ──────────────────────────────────────────
    async def list_subscribers(self, newsletter_id, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_SUBSCRIBERS, newsletter_id, limit, offset),
            NewsletterSubscriber,
        )

    async def get_subscriber(self, sid):
        return self._one(
            NewsletterSubscriber, await self.find_one(Q.GET_SUBSCRIBER, sid)
        )

    async def get_subscriber_by_email(self, newsletter_id, email):
        return self._one(
            NewsletterSubscriber,
            await self.find_one(Q.GET_SUBSCRIBER_BY_EMAIL, newsletter_id, email),
        )

    async def create_subscriber(
        self, sid, newsletter_id, email, first_name, last_name, source, status
    ):
        await self.execute(
            Q.INSERT_SUBSCRIBER,
            sid,
            newsletter_id,
            email,
            first_name,
            last_name,
            source,
            status,
        )

    async def update_subscriber_status(self, sid, status):
        await self.execute(Q.UPDATE_SUBSCRIBER_STATUS, status, status, sid)

    async def delete_subscriber(self, sid):
        await self.execute(Q.DELETE_SUBSCRIBER, sid)

    # ── Issues ───────────────────────────────────────────────
    async def list_issues(self, newsletter_id, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_ISSUES, newsletter_id, limit, offset),
            NewsletterIssue,
        )

    async def get_issue(self, iid):
        return self._one(NewsletterIssue, await self.find_one(Q.GET_ISSUE, iid))

    async def create_issue(
        self,
        iid,
        newsletter_id,
        subject,
        preview_text,
        body_html,
        body_text,
        issue_type,
        article_ids,
        status,
        scheduled_at,
        created_by,
    ):
        await self.execute(
            Q.INSERT_ISSUE,
            iid,
            newsletter_id,
            subject,
            preview_text,
            body_html,
            body_text,
            issue_type,
            json.dumps(article_ids),
            status,
            scheduled_at,
            created_by,
        )

    async def update_issue(
        self,
        iid,
        subject,
        preview_text,
        body_html,
        body_text,
        issue_type,
        article_ids,
        status,
        scheduled_at,
    ):
        await self.execute(
            Q.UPDATE_ISSUE,
            subject,
            preview_text,
            body_html,
            body_text,
            issue_type,
            json.dumps(article_ids),
            status,
            scheduled_at,
            iid,
        )

    async def update_issue_status(self, iid, status):
        await self.execute(Q.UPDATE_ISSUE_STATUS, status, status, iid)

    async def delete_issue(self, iid):
        await self.execute(Q.DELETE_ISSUE, iid)

    # ── Issue Articles ───────────────────────────────────────
    async def list_issue_articles(self, issue_id):
        return self._many(
            await self.find_all(Q.LIST_ISSUE_ARTICLES, issue_id), NewsletterIssueArticle
        )

    async def add_issue_article(self, issue_id, article_id, sort_order, blurb):
        await self.execute(
            Q.INSERT_ISSUE_ARTICLE, issue_id, article_id, sort_order, blurb
        )

    async def remove_issue_article(self, issue_id, article_id):
        await self.execute(Q.DELETE_ISSUE_ARTICLE, issue_id, article_id)

    # ── Send Events ──────────────────────────────────────────
    async def list_send_events(self, issue_id, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_SEND_EVENTS, issue_id, limit, offset),
            NewsletterSendEvent,
        )

    async def create_send_event(
        self, eid, issue_id, subscriber_id, event_type, link_url, metadata
    ):
        await self.execute(
            Q.INSERT_SEND_EVENT,
            eid,
            issue_id,
            subscriber_id,
            event_type,
            link_url,
            json.dumps(metadata),
        )

    # ── Segments ─────────────────────────────────────────────
    async def list_segments(self, newsletter_id):
        return self._many(
            await self.find_all(Q.LIST_SEGMENTS, newsletter_id), NewsletterSegment
        )

    async def get_segment(self, sid):
        return self._one(NewsletterSegment, await self.find_one(Q.GET_SEGMENT, sid))

    async def create_segment(self, sid, newsletter_id, name, filter_rules):
        await self.execute(
            Q.INSERT_SEGMENT, sid, newsletter_id, name, json.dumps(filter_rules)
        )

    async def update_segment(self, sid, name, filter_rules):
        await self.execute(Q.UPDATE_SEGMENT, name, json.dumps(filter_rules), sid)

    async def delete_segment(self, sid):
        await self.execute(Q.DELETE_SEGMENT, sid)
