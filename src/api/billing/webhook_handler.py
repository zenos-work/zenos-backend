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

        # Minimal action mapping. Business side-effects are intentionally
        # idempotent + delegated to asynchronous reconciliation where needed.
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
        return {"event_id": evt_id, "event_type": evt_type, "status": status}
