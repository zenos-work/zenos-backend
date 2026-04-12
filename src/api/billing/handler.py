"""Phase 12 Step 47 — Billing handler."""

from utils.helpers import json_resp, error
from middleware.auth import get_user, require_role
from api.billing.webhook_handler import StripeWebhookHandler
from api.billing.reconciliation import BillingReconciliation
from api.feature_flags.service import FeatureFlagService


async def _is_feature_enabled(env, ctx, user, flag_key: str) -> bool:
    if getattr(env, "DB", None) is None:
        return True
    try:
        svc = FeatureFlagService(env, ctx)
        return await svc.evaluate_one(
            flag_key,
            user_id=user.get("sub"),
            user_role=user.get("role", ""),
        )
    except Exception:
        return False


async def handle_billing(request, env, path, method, query, ctx):
    webhook = StripeWebhookHandler(env.DB, ctx)
    recon = BillingReconciliation(env.DB, ctx)
    parts = path.rstrip("/").split("/")

    # Stripe webhook endpoint is intentionally unauthenticated; security is
    # based on Stripe-Signature verification.
    if path.rstrip("/") == "/api/billing/webhooks/stripe" and method == "POST":
        signature = request.headers.get("Stripe-Signature", "")
        body = await request.json()
        payload = body if isinstance(body, dict) else {}
        secret = getattr(env, "STRIPE_WEBHOOK_SECRET", "")
        try:
            result = await webhook.process_event(payload, signature, secret)
            return json_resp(result)
        except ValueError as e:
            return error(str(e), 400)

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)

    if not require_role(user, ("SUPERADMIN",)):
        return error("Forbidden", 403)

    if not await _is_feature_enabled(env, ctx, user, "admin_billing"):
        return error("Feature 'admin_billing' is disabled", 403)

    # GET /api/admin/billing/reconciliation/:period
    if path.startswith("/api/admin/billing/reconciliation/") and method == "GET":
        period = parts[5] if len(parts) > 5 else ""
        return json_resp(await recon.report(period))

    # POST /api/admin/billing/reconcile
    if path.rstrip("/") == "/api/admin/billing/reconcile" and method == "POST":
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        period = data.get("period", "")
        threshold = int(data.get("threshold_cents", 1000) or 1000)
        if not period:
            return error("period is required", 400)
        return json_resp(await recon.reconcile(period, threshold))

    return error("Not found", 404)
