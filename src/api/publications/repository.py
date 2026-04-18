"""Phase 7 Step 30 — Publication repository."""

import json
from db.repository import BaseRepository
from api.publications import queries as Q
from models.publication.model import (
    NewsletterSubscription,
    PublicationIssue,
    PublicationIssueItem,
    PublicationGenerationRun,
    PublicationDelivery,
)


class PublicationRepository(BaseRepository):
    def _one(self, cls, row):
        return self.map_one(row, cls)

    def _many(self, rows, cls):
        return self.map_many(rows, cls)

    # ── Newsletter Subscriptions ─────────────────────────────
    async def list_subscriptions(self, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_SUBSCRIPTIONS, limit, offset),
            NewsletterSubscription,
        )

    async def get_subscription(self, sid):
        return self._one(
            NewsletterSubscription, await self.find_one(Q.GET_SUBSCRIPTION, sid)
        )

    async def get_subscription_by_email(self, email):
        return self._one(
            NewsletterSubscription,
            await self.find_one(Q.GET_SUBSCRIPTION_BY_EMAIL, email),
        )

    async def create_subscription(self, sid, email, status, source):
        await self.execute(Q.INSERT_SUBSCRIPTION, sid, email, status, source)

    async def update_subscription_status(self, sid, status):
        await self.execute(Q.UPDATE_SUBSCRIPTION_STATUS, status, status, sid)

    async def delete_subscription(self, sid):
        await self.execute(Q.DELETE_SUBSCRIPTION, sid)

    # ── Publication Issues ───────────────────────────────────
    async def list_issues(self, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_PUB_ISSUES, limit, offset), PublicationIssue
        )

    async def list_issues_by_type(self, issue_type, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_PUB_ISSUES_BY_TYPE, issue_type, limit, offset),
            PublicationIssue,
        )

    async def get_issue(self, iid):
        return self._one(PublicationIssue, await self.find_one(Q.GET_PUB_ISSUE, iid))

    async def create_issue(
        self,
        iid,
        issue_type,
        title,
        slug,
        period_start,
        period_end,
        status,
        editorial_preface,
        toc_json,
        cover_article_id,
        created_by_user_id,
    ):
        await self.execute(
            Q.INSERT_PUB_ISSUE,
            iid,
            issue_type,
            title,
            slug,
            period_start,
            period_end,
            status,
            editorial_preface,
            json.dumps(toc_json),
            cover_article_id,
            created_by_user_id,
        )

    async def update_issue(
        self,
        iid,
        title,
        editorial_preface,
        toc_json,
        status,
        total_pages,
        pdf_r2_key,
        pdf_url,
    ):
        await self.execute(
            Q.UPDATE_PUB_ISSUE,
            title,
            editorial_preface,
            json.dumps(toc_json),
            status,
            total_pages,
            pdf_r2_key,
            pdf_url,
            iid,
        )

    async def approve_issue(self, iid, approved_by):
        await self.execute(Q.APPROVE_PUB_ISSUE, approved_by, iid)

    async def publish_issue(self, iid):
        await self.execute(Q.PUBLISH_PUB_ISSUE, iid)

    async def delete_issue(self, iid):
        await self.execute(Q.DELETE_PUB_ISSUE, iid)

    # ── Issue Items ──────────────────────────────────────────
    async def list_items(self, issue_id):
        return self._many(
            await self.find_all(Q.LIST_PUB_ITEMS, issue_id), PublicationIssueItem
        )

    async def get_item(self, item_id):
        return self._one(
            PublicationIssueItem, await self.find_one(Q.GET_PUB_ITEM, item_id)
        )

    async def create_item(
        self,
        item_id,
        issue_id,
        article_id,
        section,
        position,
        item_type,
        title,
        excerpt,
        include_full_content,
    ):
        await self.execute(
            Q.INSERT_PUB_ITEM,
            item_id,
            issue_id,
            article_id,
            section,
            position,
            item_type,
            title,
            excerpt,
            int(include_full_content),
        )

    async def update_item(
        self,
        item_id,
        section,
        position,
        item_type,
        title,
        excerpt,
        include_full_content,
    ):
        await self.execute(
            Q.UPDATE_PUB_ITEM,
            section,
            position,
            item_type,
            title,
            excerpt,
            int(include_full_content),
            item_id,
        )

    async def delete_item(self, item_id):
        await self.execute(Q.DELETE_PUB_ITEM, item_id)

    # ── Generation Runs ──────────────────────────────────────
    async def list_gen_runs(self, issue_id):
        return self._many(
            await self.find_all(Q.LIST_GEN_RUNS, issue_id), PublicationGenerationRun
        )

    async def get_gen_run(self, rid):
        return self._one(
            PublicationGenerationRun, await self.find_one(Q.GET_GEN_RUN, rid)
        )

    async def create_gen_run(self, rid, issue_id, job_name, trigger_source, status):
        await self.execute(
            Q.INSERT_GEN_RUN, rid, issue_id, job_name, trigger_source, status
        )

    async def update_gen_run(self, rid, status, error_text, metrics_json):
        await self.execute(
            Q.UPDATE_GEN_RUN, status, status, error_text, json.dumps(metrics_json), rid
        )

    # ── Deliveries ───────────────────────────────────────────
    async def list_deliveries(self, issue_id, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_DELIVERIES, issue_id, limit, offset),
            PublicationDelivery,
        )

    async def get_delivery(self, did):
        return self._one(PublicationDelivery, await self.find_one(Q.GET_DELIVERY, did))

    async def create_delivery(self, did, issue_id, email, channel, status):
        await self.execute(Q.INSERT_DELIVERY, did, issue_id, email, channel, status)

    async def update_delivery_status(
        self, did, status, provider, provider_message_id, error_text
    ):
        await self.execute(
            Q.UPDATE_DELIVERY_STATUS,
            status,
            provider,
            provider_message_id,
            error_text,
            status,
            did,
        )
