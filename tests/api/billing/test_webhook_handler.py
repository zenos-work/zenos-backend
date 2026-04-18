import hashlib
import hmac
import importlib
import json

import pytest


webhook_module = importlib.import_module("api.billing.webhook_handler")
queries = importlib.import_module("api.billing.queries")


class _Handler(webhook_module.StripeWebhookHandler):
    def __init__(self):
        super().__init__(db=object(), ctx=None)
        self.exec_calls = []
        self.find_map = {}

    async def execute(self, query, *params):
        self.exec_calls.append((query, params))
        return None

    async def find_one(self, query, *params):
        return self.find_map.get((query, params))


def _sig(payload: dict, ts: str, secret: str) -> tuple[str, str]:
    payload_str = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    digest = hmac.new(
        secret.encode("utf-8"), f"{ts}.{payload_str}".encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return payload_str, f"t={ts},v1={digest}"


class TestStripeWebhookHandler:
    def test_verify_signature_success_and_failures(self):
        h = _Handler()
        payload_str = '{"a":1}'
        ts = "1711111111"
        secret = "whsec_test"
        good = hmac.new(
            secret.encode("utf-8"),
            f"{ts}.{payload_str}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        assert h.verify_signature(payload_str, f"t={ts},v1={good}", secret) is True
        assert h.verify_signature(payload_str, "", secret) is False
        assert h.verify_signature(payload_str, f"t={ts}", secret) is False
        assert h.verify_signature(payload_str, f"v1={good}", secret) is False

    @pytest.mark.asyncio
    async def test_process_event_invalid_signature_raises(self):
        h = _Handler()
        with pytest.raises(ValueError, match="Invalid Stripe signature"):
            await h.process_event(
                {"id": "evt_1", "type": "invoice.paid"}, "bad", "secret"
            )

    @pytest.mark.asyncio
    async def test_process_event_missing_id_or_type_raises(self):
        h = _Handler()
        payload = {"id": "", "type": ""}
        _, header = _sig(payload, "1711111111", "whsec_test")
        with pytest.raises(ValueError, match="Invalid event payload"):
            await h.process_event(payload, header, "whsec_test")

    @pytest.mark.asyncio
    async def test_process_event_activation_path(self):
        h = _Handler()
        payload = {
            "id": "evt_1",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "metadata": {"user_id": "u1", "plan_tier": "team_suite"},
                    "customer": "cus_1",
                    "subscription": "sub_1",
                }
            },
        }
        h.find_map[(queries.FIND_USER_BY_ID, ("u1",))] = {"id": "u1"}
        _, header = _sig(payload, "1711111111", "whsec_test")

        result = await h.process_event(payload, header, "whsec_test")

        assert result["status"] == "processed"
        assert result["actions"][0]["type"] == "membership_activated"
        assert result["actions"][0]["user_id"] == "u1"

        used_queries = [q for q, _ in h.exec_calls]
        assert queries.INSERT_STRIPE_EVENT in used_queries
        assert queries.ACTIVATE_USER_MEMBERSHIP in used_queries
        assert queries.UPDATE_STRIPE_EVENT_STATUS in used_queries

    @pytest.mark.asyncio
    async def test_process_event_cancellation_and_ignored_paths(self):
        h = _Handler()

        cancel_payload = {
            "id": "evt_2",
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": "sub_42"}},
        }
        _, cancel_header = _sig(cancel_payload, "1711111112", "whsec_test")
        cancel_result = await h.process_event(
            cancel_payload, cancel_header, "whsec_test"
        )
        assert cancel_result["status"] == "processed"
        assert cancel_result["actions"][0]["type"] == "membership_cancelled"

        ignored_payload = {
            "id": "evt_3",
            "type": "customer.created",
            "data": {"object": {}},
        }
        _, ignored_header = _sig(ignored_payload, "1711111113", "whsec_test")
        ignored_result = await h.process_event(
            ignored_payload, ignored_header, "whsec_test"
        )
        assert ignored_result["status"] == "ignored"
        assert ignored_result["actions"] == []

    @pytest.mark.asyncio
    async def test_resolve_user_id_fallback_order(self):
        h = _Handler()

        h.find_map[(queries.FIND_USER_BY_ID, ("u-meta",))] = {"id": "u-meta"}
        got_meta = await h._resolve_user_id_from_event(
            {"metadata": {"user_id": "u-meta"}}
        )
        assert got_meta == "u-meta"

        h.find_map[(queries.FIND_USER_BY_EMAIL, ("e@test.io",))] = {"id": "u-email"}
        got_email = await h._resolve_user_id_from_event({"customer_email": "e@test.io"})
        assert got_email == "u-email"

        h.find_map[(queries.FIND_USER_BY_STRIPE_CUSTOMER, ("cus_9",))] = {
            "id": "u-customer"
        }
        got_customer = await h._resolve_user_id_from_event({"customer": "cus_9"})
        assert got_customer == "u-customer"

        got_none = await h._resolve_user_id_from_event({})
        assert got_none == ""

    @pytest.mark.asyncio
    async def test_activate_and_cancel_helpers_edge_cases(self):
        h = _Handler()

        no_user = await h._activate_membership_from_event(
            {"metadata": {"user_id": "missing"}}
        )
        assert no_user is None

        no_sub = await h._cancel_membership_from_event({})
        assert no_sub is None
