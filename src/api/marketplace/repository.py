"""Phase 9 Step 33 — Marketplace repository."""

import json
from db.repository import BaseRepository
from api.marketplace import queries as Q
from models.marketplace.model import (
    MarketplaceItem,
    MarketplacePurchase,
    MarketplaceReview,
)


class MarketplaceRepository(BaseRepository):
    def _one(self, cls, row):
        return self.map_one(row, cls)

    def _many(self, rows, cls):
        return self.map_many(rows, cls)

    # ── Items ────────────────────────────────────────────────
    async def list_items(self, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_ITEMS, limit, offset), MarketplaceItem
        )

    async def list_items_by_seller(self, seller_id, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_ITEMS_BY_SELLER, seller_id, limit, offset),
            MarketplaceItem,
        )

    async def list_items_by_category(self, category, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_ITEMS_BY_CATEGORY, category, limit, offset),
            MarketplaceItem,
        )

    async def get_item(self, iid):
        return self._one(MarketplaceItem, await self.find_one(Q.GET_ITEM, iid))

    async def create_item(
        self,
        iid,
        seller_id,
        org_id,
        name,
        slug,
        short_desc,
        long_desc,
        item_type,
        category,
        price_cents,
        currency,
        pricing_model,
        preview_images,
        asset_url,
        workflow_id,
        status,
    ):
        await self.execute(
            Q.INSERT_ITEM,
            iid,
            seller_id,
            org_id,
            name,
            slug,
            short_desc,
            long_desc,
            item_type,
            category,
            price_cents,
            currency,
            pricing_model,
            json.dumps(preview_images),
            asset_url,
            workflow_id,
            status,
        )

    async def update_item(
        self,
        iid,
        name,
        short_desc,
        long_desc,
        item_type,
        category,
        price_cents,
        currency,
        pricing_model,
        preview_images,
        asset_url,
        workflow_id,
        status,
    ):
        await self.execute(
            Q.UPDATE_ITEM,
            name,
            short_desc,
            long_desc,
            item_type,
            category,
            price_cents,
            currency,
            pricing_model,
            json.dumps(preview_images),
            asset_url,
            workflow_id,
            status,
            iid,
        )

    async def delete_item(self, iid):
        await self.execute(Q.DELETE_ITEM, iid)

    async def publish_item(self, iid):
        await self.execute(Q.PUBLISH_ITEM, iid)

    async def increment_purchase_count(self, iid):
        await self.execute(Q.INCREMENT_PURCHASE_COUNT, iid)

    async def update_rating(self, iid, rating):
        await self.execute(Q.UPDATE_RATING, rating, iid)

    # ── Purchases ────────────────────────────────────────────
    async def list_purchases_by_buyer(self, buyer_id, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_PURCHASES_BY_BUYER, buyer_id, limit, offset),
            MarketplacePurchase,
        )

    async def list_purchases_by_item(self, item_id, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_PURCHASES_BY_ITEM, item_id, limit, offset),
            MarketplacePurchase,
        )

    async def get_purchase(self, pid):
        return self._one(MarketplacePurchase, await self.find_one(Q.GET_PURCHASE, pid))

    async def get_purchase_by_buyer_item(self, item_id, buyer_id):
        return self._one(
            MarketplacePurchase,
            await self.find_one(Q.GET_PURCHASE_BY_BUYER_ITEM, item_id, buyer_id),
        )

    async def create_purchase(
        self,
        pid,
        item_id,
        buyer_id,
        org_id,
        payment_id,
        price_paid_cents,
        currency,
        status,
    ):
        await self.execute(
            Q.INSERT_PURCHASE,
            pid,
            item_id,
            buyer_id,
            org_id,
            payment_id,
            price_paid_cents,
            currency,
            status,
        )

    # ── Reviews ──────────────────────────────────────────────
    async def list_reviews(self, item_id, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_REVIEWS, item_id, limit, offset),
            MarketplaceReview,
        )

    async def get_review(self, rid):
        return self._one(MarketplaceReview, await self.find_one(Q.GET_REVIEW, rid))

    async def get_review_by_reviewer(self, item_id, reviewer_id):
        return self._one(
            MarketplaceReview,
            await self.find_one(Q.GET_REVIEW_BY_REVIEWER, item_id, reviewer_id),
        )

    async def create_review(self, rid, item_id, reviewer_id, rating, body):
        await self.execute(Q.INSERT_REVIEW, rid, item_id, reviewer_id, rating, body)

    async def delete_review(self, rid):
        await self.execute(Q.DELETE_REVIEW, rid)
