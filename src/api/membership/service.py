"""Premium and membership service for Phase 3 (GAP-015, GAP-016, GAP-017)"""

import json
from datetime import datetime
from db.executor import D1Executor


class MembershipService:
    """Handle membership checks, paywall enforcement, and premium tracking."""

    def __init__(self, env, ctx=None):
        # Handle test environments where DB might not be available
        db = getattr(env, "DB", None)
        self._db = D1Executor(db, ctx) if db else None
        self._raw_db = db
        self._env = env
        self._ctx = ctx

    async def _first(self, sql: str, params: list):
        if self._raw_db and hasattr(self._raw_db, "first"):
            return await self._raw_db.first(sql, params)
        return await self._db.first(sql, params)

    async def _all(self, sql: str, params: list | None = None):
        if self._raw_db and hasattr(self._raw_db, "all"):
            return await self._raw_db.all(sql, params or [])
        return await self._db.all(sql, params or [])

    async def _run(self, sql: str, params: list):
        if self._raw_db and hasattr(self._raw_db, "run"):
            return await self._raw_db.run(sql, params)
        return await self._db.run(sql, params)

    async def can_read_premium_article(self, user_id: str, article_id: str) -> bool:
        """Check if user has access to premium article."""
        if not user_id:
            return False

        # Check user membership status
        user_row = await self._first(
            "SELECT membership_status, subscription_expires_at FROM users WHERE id = ?",
            [user_id],
        )
        if not user_row:
            return False

        status = user_row.get("membership_status")
        expires_at = user_row.get("subscription_expires_at")

        # Check if membership is active and not expired
        if status == "active":
            if expires_at:
                now = datetime.utcnow().isoformat()
                if now < expires_at:
                    return True
            else:
                return True  # No expiration date = lifetime access
        return False

    async def can_publish_premium_article(self, user_id: str) -> bool:
        """Check if user can publish premium articles."""
        # Only creator_pro and team_suite can publish premium articles
        user_row = await self._first(
            "SELECT membership_tier FROM users WHERE id = ?",
            [user_id],
        )
        if not user_row:
            return False

        tier = user_row.get("membership_tier")
        return tier in ("creator_pro", "team_suite")

    async def track_premium_read(
        self,
        user_id: str,
        article_id: str,
        scroll_depth: float = 0,
        duration_seconds: int = 0,
    ) -> dict:
        """Track premium article read for analytics."""
        import uuid

        read_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        await self._run(
            """
            INSERT INTO premium_article_reads
            (id, user_id, article_id, accessed_at, scroll_depth, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                read_id,
                user_id,
                article_id,
                now,
                scroll_depth,
                duration_seconds,
            ],
        )

        # Update user's last_premium_read_at and increment read count
        await self._run(
            """
            UPDATE users
            SET last_premium_read_at = ?, premium_read_count = premium_read_count + 1
            WHERE id = ?
            """,
            [now, user_id],
        )

        return {"id": read_id, "tracked_at": now}

    async def log_premium_funnel_event(
        self,
        event_type: str,
        article_id: str,
        user_id: str = None,
        device_type: str = None,
        referrer: str = None,
        ip_hash: str = None,
    ) -> dict:
        """Log premium conversion funnel event for analytics."""
        import uuid

        event_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        await self._run(
            """
            INSERT INTO premium_funnel_events
            (id, user_id, article_id, event_type, device_type, referrer, ip_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                event_id,
                user_id,
                article_id,
                event_type,
                device_type,
                referrer,
                ip_hash,
                now,
            ],
        )

        return {"event_id": event_id, "logged_at": now}

    async def get_membership_plans(self) -> list:
        """Get all available membership plans."""
        rows = await self._all(
            "SELECT * FROM membership_plans ORDER BY price_monthly ASC"
        )
        plans = []
        for row in rows:
            plans.append(
                {
                    "id": row.get("id"),
                    "name": row.get("name"),
                    "tier": row.get("tier"),
                    "price_monthly": row.get("price_monthly"),
                    "description": row.get("description"),
                    "max_articles": row.get("max_articles"),
                    "max_premium_reads": row.get("max_premium_reads"),
                    "features": json.loads(row.get("features", "[]")),
                }
            )
        return plans

    async def get_user_membership(self, user_id: str) -> dict:
        """Get user's current membership details."""
        user_row = await self._first(
            """
            SELECT
                membership_tier,
                membership_status,
                subscription_started_at,
                subscription_expires_at
            FROM users WHERE id = ?
            """,
            [user_id],
        )

        if not user_row:
            return None

        # Check if subscription is expired
        status = user_row.get("membership_status")
        expires_at = user_row.get("subscription_expires_at")

        if status == "active" and expires_at:
            now = datetime.utcnow().isoformat()
            if now > expires_at:
                status = "expired"

        return {
            "tier": user_row.get("membership_tier"),
            "status": status,
            "started_at": user_row.get("subscription_started_at"),
            "expires_at": user_row.get("subscription_expires_at"),
            "is_active": status == "active"
            and (not expires_at or expires_at > datetime.utcnow().isoformat()),
        }

    async def upgrade_membership(
        self,
        user_id: str,
        new_tier: str,
        stripe_subscription_id: str = None,
    ) -> dict:
        """Upgrade user membership (for testing; real payments via Stripe)."""
        import uuid

        now = datetime.utcnow().isoformat()

        # Update user table
        await self._run(
            """
            UPDATE users SET
                membership_tier = ?,
                membership_status = 'active',
                subscription_started_at = ?,
                stripe_subscription_id = ?
            WHERE id = ?
            """,
            [new_tier, now, stripe_subscription_id, user_id],
        )

        # Create membership record
        membership_id = str(uuid.uuid4())
        await self._run(
            """
            INSERT INTO user_memberships
            (id, user_id, membership_tier, status, started_at, stripe_subscription_id, created_at, updated_at)
            VALUES (?, ?, ?, 'active', ?, ?, ?, ?)
            """,
            [
                membership_id,
                user_id,
                new_tier,
                now,
                stripe_subscription_id,
                now,
                now,
            ],
        )

        # Log conversion event
        await self.log_premium_funnel_event(
            event_type="membership_upgraded",
            article_id=None,
            user_id=user_id,
        )

        return {
            "membership_id": membership_id,
            "user_id": user_id,
            "tier": new_tier,
            "status": "active",
            "started_at": now,
        }
