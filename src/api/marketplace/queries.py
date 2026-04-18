"""Phase 9 Step 33 — Marketplace queries."""

# ── Items ────────────────────────────────────────────────────
LIST_ITEMS = "SELECT * FROM marketplace_items WHERE status = 'published' ORDER BY is_featured DESC, created_at DESC LIMIT ? OFFSET ?"
LIST_ITEMS_BY_SELLER = "SELECT * FROM marketplace_items WHERE seller_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
LIST_ITEMS_BY_CATEGORY = "SELECT * FROM marketplace_items WHERE category = ? AND status = 'published' ORDER BY created_at DESC LIMIT ? OFFSET ?"
GET_ITEM = "SELECT * FROM marketplace_items WHERE id = ?"
GET_ITEM_BY_SLUG = "SELECT * FROM marketplace_items WHERE slug = ?"
INSERT_ITEM = """INSERT INTO marketplace_items
    (id, seller_id, org_id, name, slug, short_desc, long_desc, item_type,
     category, price_cents, currency, pricing_model, preview_images,
     asset_url, workflow_id, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
UPDATE_ITEM = """UPDATE marketplace_items SET
    name=?, short_desc=?, long_desc=?, item_type=?, category=?,
    price_cents=?, currency=?, pricing_model=?, preview_images=?,
    asset_url=?, workflow_id=?, status=?,
    updated_at=datetime('now') WHERE id=?"""
DELETE_ITEM = "DELETE FROM marketplace_items WHERE id = ?"
PUBLISH_ITEM = "UPDATE marketplace_items SET status='published', published_at=datetime('now'), updated_at=datetime('now') WHERE id=?"
INCREMENT_PURCHASE_COUNT = (
    "UPDATE marketplace_items SET purchase_count = purchase_count + 1 WHERE id = ?"
)
UPDATE_RATING = """UPDATE marketplace_items SET
    rating_count = rating_count + 1,
    rating_avg = ((rating_avg * rating_count) + ?) / (rating_count + 1),
    updated_at=datetime('now') WHERE id=?"""

# ── Purchases ────────────────────────────────────────────────
LIST_PURCHASES_BY_BUYER = "SELECT * FROM marketplace_purchases WHERE buyer_id = ? ORDER BY purchased_at DESC LIMIT ? OFFSET ?"
LIST_PURCHASES_BY_ITEM = "SELECT * FROM marketplace_purchases WHERE item_id = ? ORDER BY purchased_at DESC LIMIT ? OFFSET ?"
GET_PURCHASE = "SELECT * FROM marketplace_purchases WHERE id = ?"
GET_PURCHASE_BY_BUYER_ITEM = (
    "SELECT * FROM marketplace_purchases WHERE item_id = ? AND buyer_id = ?"
)
INSERT_PURCHASE = """INSERT INTO marketplace_purchases
    (id, item_id, buyer_id, org_id, payment_id, price_paid_cents, currency, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""

# ── Reviews ──────────────────────────────────────────────────
LIST_REVIEWS = "SELECT * FROM marketplace_reviews WHERE item_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
GET_REVIEW = "SELECT * FROM marketplace_reviews WHERE id = ?"
GET_REVIEW_BY_REVIEWER = (
    "SELECT * FROM marketplace_reviews WHERE item_id = ? AND reviewer_id = ?"
)
INSERT_REVIEW = "INSERT INTO marketplace_reviews (id, item_id, reviewer_id, rating, body) VALUES (?, ?, ?, ?, ?)"
DELETE_REVIEW = "DELETE FROM marketplace_reviews WHERE id = ?"
