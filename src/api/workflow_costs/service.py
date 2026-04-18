"""Phase 10 Step 37 — Workflow cost service."""

from api.workflow_costs.repository import WorkflowCostRepository
from utils.helpers import new_id, paginate


class WorkflowCostService:
    def __init__(self, env, ctx=None):
        self._repo = WorkflowCostRepository(env.DB, ctx)

    # ── Rates ────────────────────────────────────────────────
    async def list_rates(self, org_id):
        items = await self._repo.list_rates(org_id)
        return [r.to_dict() for r in items]

    async def list_global_rates(self):
        items = await self._repo.list_global_rates()
        return [r.to_dict() for r in items]

    async def create_rate(
        self,
        org_id,
        node_type_id,
        cost_model="per_execution",
        rate_microcents=0,
        unit_label="",
        currency="USD",
        notes="",
    ):
        rid = new_id()
        await self._repo.create_rate(
            rid,
            org_id,
            node_type_id,
            cost_model,
            rate_microcents,
            unit_label,
            currency,
            notes,
        )
        return {"id": rid}

    async def update_rate(self, rid, **kwargs):
        existing = await self._repo.get_rate(rid)
        if not existing:
            raise ValueError("Rate not found")
        await self._repo.update_rate(
            rid,
            cost_model=kwargs.get("cost_model") or existing.cost_model,
            rate_microcents=kwargs.get("rate_microcents")
            if kwargs.get("rate_microcents") is not None
            else existing.rate_microcents,
            unit_label=kwargs.get("unit_label")
            if kwargs.get("unit_label") is not None
            else existing.unit_label,
            currency=kwargs.get("currency") or existing.currency,
            notes=kwargs.get("notes")
            if kwargs.get("notes") is not None
            else existing.notes,
        )
        return {"id": rid}

    async def delete_rate(self, rid):
        existing = await self._repo.get_rate(rid)
        if not existing:
            raise ValueError("Rate not found")
        await self._repo.delete_rate(rid)

    # ── Run Costs ────────────────────────────────────────────
    async def list_run_costs(self, run_id):
        items = await self._repo.list_run_costs(run_id)
        return [c.to_dict() for c in items]

    async def list_workflow_costs(self, workflow_id, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_workflow_costs(workflow_id, lim, off)
        return {"costs": [c.to_dict() for c in items], "page": page, "limit": lim}

    async def record_cost(
        self,
        run_id,
        step_id,
        workflow_id,
        org_id,
        node_type_id,
        cost_model,
        units_consumed=0,
        unit_label="",
        cost_microcents=0,
        cost_actual_microcents=0,
        currency="USD",
        external_ref="",
        notes="",
    ):
        cid = new_id()
        await self._repo.create_run_cost(
            cid,
            run_id,
            step_id,
            workflow_id,
            org_id,
            node_type_id,
            cost_model,
            units_consumed,
            unit_label,
            cost_microcents,
            cost_actual_microcents,
            currency,
            external_ref,
            notes,
        )
        return {"id": cid}

    # ── Summary ──────────────────────────────────────────────
    async def get_cost_summary(self, workflow_id):
        s = await self._repo.get_cost_summary(workflow_id)
        if not s:
            raise ValueError("Summary not found")
        return s.to_dict()

    async def list_cost_summaries(self, org_id):
        items = await self._repo.list_cost_summaries(org_id)
        return [s.to_dict() for s in items]

    # ── Monthly Rollup ───────────────────────────────────────
    async def get_monthly_rollup(self, org_id, year_month):
        r = await self._repo.get_monthly_rollup(org_id, year_month)
        if not r:
            raise ValueError("Rollup not found")
        return r.to_dict()

    async def list_monthly_rollups(self, org_id, page=1, limit=12):
        lim, off = paginate(page, limit)
        items = await self._repo.list_monthly_rollups(org_id, lim, off)
        return {"rollups": [r.to_dict() for r in items], "page": page, "limit": lim}

    async def set_budget_cap(self, org_id, year_month, budget_cap_microcents):
        await self._repo.set_budget_cap(org_id, year_month, budget_cap_microcents)
        return {
            "org_id": org_id,
            "year_month": year_month,
            "budget_cap_microcents": budget_cap_microcents,
        }

    async def check_budget(self, org_id, year_month):
        r = await self._repo.get_monthly_rollup(org_id, year_month)
        if not r or not r.budget_cap_microcents:
            return {"exceeded": False}
        exceeded = r.total_cost_microcents >= r.budget_cap_microcents
        return {
            "exceeded": exceeded,
            "total_cost_microcents": r.total_cost_microcents,
            "budget_cap_microcents": r.budget_cap_microcents,
        }
