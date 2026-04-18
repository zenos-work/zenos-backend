"""Phase 9 Step 33 — Marketplace service."""

from api.marketplace.repository import MarketplaceRepository
from utils.helpers import new_id, paginate


class MarketplaceService:
    def __init__(self, env, ctx=None):
        self._repo = MarketplaceRepository(env.DB, ctx)

    # ── Items ────────────────────────────────────────────────
    async def list_items(self, page=1, limit=20, category=None, seller_id=None):
        lim, off = paginate(page, limit)
        if seller_id:
            items = await self._repo.list_items_by_seller(seller_id, lim, off)
        elif category:
            items = await self._repo.list_items_by_category(category, lim, off)
        else:
            items = await self._repo.list_items(lim, off)
        return {"items": [i.to_dict() for i in items], "page": page, "limit": lim}

    async def get_item(self, iid):
        item = await self._repo.get_item(iid)
        if not item:
            raise ValueError("Item not found")
        return item.to_dict()

    async def create_item(
        self,
        seller_id,
        name,
        slug,
        short_desc,
        category,
        org_id="",
        long_desc="",
        item_type="",
        price_cents=0,
        currency="USD",
        pricing_model="one_time",
        preview_images=None,
        asset_url="",
        workflow_id="",
        status="draft",
    ):
        iid = new_id()
        await self._repo.create_item(
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
            preview_images or [],
            asset_url,
            workflow_id,
            status,
        )
        return {"id": iid}

    async def update_item(self, iid, **kwargs):
        existing = await self._repo.get_item(iid)
        if not existing:
            raise ValueError("Item not found")
        await self._repo.update_item(
            iid,
            name=kwargs.get("name") or existing.name,
            short_desc=kwargs.get("short_desc") or existing.short_desc,
            long_desc=kwargs.get("long_desc")
            if kwargs.get("long_desc") is not None
            else existing.long_desc,
            item_type=kwargs.get("item_type") or existing.item_type,
            category=kwargs.get("category") or existing.category,
            price_cents=kwargs.get("price_cents")
            if kwargs.get("price_cents") is not None
            else existing.price_cents,
            currency=kwargs.get("currency") or existing.currency,
            pricing_model=kwargs.get("pricing_model") or existing.pricing_model,
            preview_images=kwargs.get("preview_images")
            if kwargs.get("preview_images") is not None
            else existing.preview_images,
            asset_url=kwargs.get("asset_url")
            if kwargs.get("asset_url") is not None
            else existing.asset_url,
            workflow_id=kwargs.get("workflow_id")
            if kwargs.get("workflow_id") is not None
            else existing.workflow_id,
            status=kwargs.get("status") or existing.status,
        )
        return {"id": iid}

    async def delete_item(self, iid):
        existing = await self._repo.get_item(iid)
        if not existing:
            raise ValueError("Item not found")
        await self._repo.delete_item(iid)

    async def publish_item(self, iid):
        existing = await self._repo.get_item(iid)
        if not existing:
            raise ValueError("Item not found")
        await self._repo.publish_item(iid)
        return {"id": iid, "status": "published"}

    # ── Purchases ────────────────────────────────────────────
    async def list_purchases(self, buyer_id, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_purchases_by_buyer(buyer_id, lim, off)
        return {"purchases": [p.to_dict() for p in items], "page": page, "limit": lim}

    async def list_item_purchases(self, item_id, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_purchases_by_item(item_id, lim, off)
        return {"purchases": [p.to_dict() for p in items], "page": page, "limit": lim}

    async def purchase_item(
        self,
        item_id,
        buyer_id,
        org_id="",
        payment_id="",
        price_paid_cents=0,
        currency="USD",
    ):
        existing = await self._repo.get_purchase_by_buyer_item(item_id, buyer_id)
        if existing:
            raise ValueError("Already purchased")
        pid = new_id()
        await self._repo.create_purchase(
            pid,
            item_id,
            buyer_id,
            org_id,
            payment_id,
            price_paid_cents,
            currency,
            "completed",
        )
        await self._repo.increment_purchase_count(item_id)
        return {"id": pid}

    # ── Reviews ──────────────────────────────────────────────
    async def list_reviews(self, item_id, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_reviews(item_id, lim, off)
        return {"reviews": [r.to_dict() for r in items], "page": page, "limit": lim}

    async def create_review(self, item_id, reviewer_id, rating, body=""):
        existing = await self._repo.get_review_by_reviewer(item_id, reviewer_id)
        if existing:
            raise ValueError("Already reviewed")
        rid = new_id()
        await self._repo.create_review(rid, item_id, reviewer_id, rating, body)
        await self._repo.update_rating(item_id, rating)
        return {"id": rid}

    async def delete_review(self, rid):
        existing = await self._repo.get_review(rid)
        if not existing:
            raise ValueError("Review not found")
        await self._repo.delete_review(rid)
