"""Phase 12 Step 47 — Stripe webhook processor."""

import hmac
import hashlib
import json

from db.repository import BaseRepository
from api.billing import queries as Q
from utils.helpers import new_id


class StripeWebhookHandler(BaseRepository):
    def __init__(self, db, ctx=None):
        super().__init__(db, ctx)

    def verify_signature(
        self, payload: str, signature_header: str, secret: str
    ) -> bool:
        """Verify Stripe-style signature header with HMAC SHA-256.

        Expected header shape: "t=<timestamp>,v1=<hexsig>"
        Signed payload shape: "<timestamp>.<payload>"
        """
        if not signature_header or not secret:
            return False

        parts = {}
        for part in signature_header.split(","):
            if "=" not in part:
                continue
            k, v = part.split("=", 1)
            parts[k.strip()] = v.strip()

        timestamp = parts.get("t", "")
        given_sig = parts.get("v1", "")
        if not timestamp or not given_sig:
            return False

        signed_payload = f"{timestamp}.{payload}".encode("utf-8")
        expected_sig = hmac.new(
            secret.encode("utf-8"),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected_sig, given_sig)

    async def process_event(
        self, payload: dict, signature_header: str, secret: str
    ) -> dict:
        payload_str = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        if not self.verify_signature(payload_str, signature_header, secret):
            raise ValueError("Invalid Stripe signature")

        evt_id = payload.get("id", "")
        evt_type = payload.get("type", "")
        if not evt_id or not evt_type:
            raise ValueError("Invalid event payload")

        await self.execute(
            Q.INSERT_STRIPE_EVENT,
            new_id(),
            evt_id,
            evt_type,
            payload_str,
            signature_header,
            "received",
        )

        obj = (payload.get("data") or {}).get("object") or {}
        actions = []

        if evt_type in {"checkout.session.completed", "customer.subscription.updated"}:
            activation = await self._activate_membership_from_event(obj)
            if activation:
                actions.append(activation)

        if evt_type in {"customer.subscription.deleted", "invoice.payment_failed"}:
            cancellation = await self._cancel_membership_from_event(obj)
            if cancellation:
                actions.append(cancellation)

        status = "processed"
        if evt_type in {
            "checkout.session.completed",
            "invoice.paid",
            "invoice.payment_failed",
            "customer.subscription.deleted",
            "customer.subscription.updated",
            "payout.paid",
        }:
            status = "processed"
        else:
            status = "ignored"

        await self.execute(Q.UPDATE_STRIPE_EVENT_STATUS, status, evt_id)
        return {
            "event_id": evt_id,
            "event_type": evt_type,
            "status": status,
            "actions": actions,
        }

    async def _resolve_user_id_from_event(self, obj: dict) -> str:
        metadata = obj.get("metadata") or {}
        user_id = metadata.get("user_id") or obj.get("client_reference_id") or ""
        if user_id:
            row = await self.find_one(Q.FIND_USER_BY_ID, user_id)
            if row:
                return row.get("id") or ""

        customer_email = obj.get("customer_email") or ""
        if customer_email:
            row = await self.find_one(Q.FIND_USER_BY_EMAIL, customer_email)
            if row:
                return row.get("id") or ""

        customer_id = obj.get("customer") or ""
        if customer_id:
            row = await self.find_one(Q.FIND_USER_BY_STRIPE_CUSTOMER, customer_id)
            if row:
                return row.get("id") or ""

        return ""

    async def _activate_membership_from_event(self, obj: dict) -> dict | None:
        user_id = await self._resolve_user_id_from_event(obj)
        if not user_id:
            return None

        metadata = obj.get("metadata") or {}
        tier = (
            metadata.get("plan_tier")
            or metadata.get("membership_tier")
            or "creator_pro"
        )
        stripe_customer_id = obj.get("customer") or None
        stripe_subscription_id = (
            obj.get("subscription") or metadata.get("stripe_subscription_id") or None
        )

        await self.execute(
            Q.ACTIVATE_USER_MEMBERSHIP,
            tier,
            stripe_customer_id,
            stripe_subscription_id,
            user_id,
        )

        if stripe_subscription_id:
            await self.execute(
                Q.UPDATE_USER_MEMBERSHIP_STATUS_BY_SUBSCRIPTION,
                "active",
                "active",
                stripe_subscription_id,
            )
            await self.execute(
                Q.UPSERT_USER_MEMBERSHIP_BY_SUBSCRIPTION,
                new_id(),
                user_id,
                tier,
                stripe_subscription_id,
            )

        return {
            "type": "membership_activated",
            "user_id": user_id,
            "tier": tier,
            "stripe_subscription_id": stripe_subscription_id,
        }

    async def _cancel_membership_from_event(self, obj: dict) -> dict | None:
        stripe_subscription_id = obj.get("subscription") or obj.get("id") or ""
        if not stripe_subscription_id:
            return None

        await self.execute(Q.CANCEL_USER_MEMBERSHIP, stripe_subscription_id)
        await self.execute(
            Q.UPDATE_USER_MEMBERSHIP_STATUS_BY_SUBSCRIPTION,
            "cancelled",
            "cancelled",
            stripe_subscription_id,
        )

        return {
            "type": "membership_cancelled",
            "stripe_subscription_id": stripe_subscription_id,
        }
