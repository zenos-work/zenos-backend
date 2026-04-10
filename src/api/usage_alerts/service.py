"""Phase 10 Steps 39-40 — Usage, alerts & quota service."""

from api.usage_alerts.repository import UsageAlertRepository
from utils.helpers import new_id


class UsageAlertService:
    def __init__(self, env, ctx=None):
        self._repo = UsageAlertRepository(env.DB, ctx)

    # ── Alert Rules ──────────────────────────────────────────
    async def list_alert_rules(self, org_id):
        items = await self._repo.list_alert_rules(org_id)
        return [r.to_dict() for r in items]

    async def get_alert_rule(self, rid):
        r = await self._repo.get_alert_rule(rid)
        if not r:
            raise ValueError("Alert rule not found")
        return r.to_dict()

    async def create_alert_rule(
        self,
        org_id,
        created_by,
        name,
        alert_type,
        config=None,
        threshold_value=0,
        comparison="gte",
        notify_channels=None,
        notify_user_ids=None,
        cooldown_minutes=60,
        is_active=True,
    ):
        rid = new_id()
        await self._repo.create_alert_rule(
            rid,
            org_id,
            created_by,
            name,
            alert_type,
            config or {},
            threshold_value,
            comparison,
            notify_channels or ["in_app"],
            notify_user_ids or [],
            cooldown_minutes,
            is_active,
        )
        return {"id": rid}

    async def update_alert_rule(self, rid, **kwargs):
        existing = await self._repo.get_alert_rule(rid)
        if not existing:
            raise ValueError("Alert rule not found")
        await self._repo.update_alert_rule(
            rid,
            name=kwargs.get("name") or existing.name,
            alert_type=kwargs.get("alert_type") or existing.alert_type,
            config=kwargs.get("config")
            if kwargs.get("config") is not None
            else existing.config,
            threshold_value=kwargs.get("threshold_value")
            if kwargs.get("threshold_value") is not None
            else existing.threshold_value,
            comparison=kwargs.get("comparison") or existing.comparison,
            notify_channels=kwargs.get("notify_channels")
            if kwargs.get("notify_channels") is not None
            else existing.notify_channels,
            notify_user_ids=kwargs.get("notify_user_ids")
            if kwargs.get("notify_user_ids") is not None
            else existing.notify_user_ids,
            cooldown_minutes=kwargs.get("cooldown_minutes")
            if kwargs.get("cooldown_minutes") is not None
            else existing.cooldown_minutes,
            is_active=kwargs.get("is_active")
            if kwargs.get("is_active") is not None
            else existing.is_active,
        )
        return {"id": rid}

    async def delete_alert_rule(self, rid):
        existing = await self._repo.get_alert_rule(rid)
        if not existing:
            raise ValueError("Alert rule not found")
        await self._repo.delete_alert_rule(rid)

    async def toggle_alert_rule(self, rid):
        existing = await self._repo.get_alert_rule(rid)
        if not existing:
            raise ValueError("Alert rule not found")
        new_state = not existing.is_active
        await self._repo.toggle_alert_rule(rid, new_state)
        return {"id": rid, "is_active": new_state}

    # ── Quota (Step 39) ─────────────────────────────────────
    async def check_quota(self, org_id, year_month):
        limit = await self._repo.get_org_workflow_limit(org_id)
        used = await self._repo.get_org_monthly_runs(org_id, year_month)
        exceeded = limit > 0 and used >= limit
        return {
            "org_id": org_id,
            "year_month": year_month,
            "limit": limit,
            "used": used,
            "exceeded": exceeded,
            "remaining": max(0, limit - used) if limit > 0 else None,
        }

    # ── Usage Export (Step 40) ───────────────────────────────
    async def export_usage_csv(self, org_id):
        """Return list-of-dicts representation for CSV export."""
        from api.workflow_costs.repository import WorkflowCostRepository

        cost_repo = WorkflowCostRepository(self._repo._ex._db, None)
        summaries = await cost_repo.list_cost_summaries(org_id)
        rows = []
        for s in summaries:
            rows.append(
                {
                    "workflow_id": s.workflow_id,
                    "total_runs_costed": s.total_runs_costed,
                    "total_cost_microcents": s.total_cost_microcents,
                    "ad_spend_microcents": s.total_ad_spend_microcents,
                    "ai_cost_microcents": s.total_ai_cost_microcents,
                    "email_cost_microcents": s.total_email_cost_microcents,
                    "avg_run_cost_microcents": s.avg_run_cost_microcents,
                }
            )
        return rows
