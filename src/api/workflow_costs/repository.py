"""Phase 10 Step 37 — Workflow cost repository."""

from db.repository import BaseRepository
from api.workflow_costs import queries as Q
from models.workflow_cost.model import (
    WorkflowNodeCostRate,
    WorkflowRunCost,
    WorkflowCostSummary,
    OrgCostMonthlyRollup,
)


class WorkflowCostRepository(BaseRepository):
    def _one(self, cls, row):
        return self.map_one(row, cls)

    def _many(self, rows, cls):
        return self.map_many(rows, cls)

    # ── Rates ────────────────────────────────────────────────
    async def list_rates(self, org_id):
        return self._many(
            await self.find_all(Q.LIST_RATES, org_id), WorkflowNodeCostRate
        )

    async def list_global_rates(self):
        return self._many(
            await self.find_all(Q.LIST_GLOBAL_RATES), WorkflowNodeCostRate
        )

    async def get_rate(self, rid):
        return self._one(WorkflowNodeCostRate, await self.find_one(Q.GET_RATE, rid))

    async def get_rate_for_node(self, org_id, node_type_id):
        return self._one(
            WorkflowNodeCostRate,
            await self.find_one(Q.GET_RATE_FOR_NODE, org_id, node_type_id),
        )

    async def create_rate(
        self,
        rid,
        org_id,
        node_type_id,
        cost_model,
        rate_microcents,
        unit_label,
        currency,
        notes,
    ):
        await self.execute(
            Q.INSERT_RATE,
            rid,
            org_id,
            node_type_id,
            cost_model,
            rate_microcents,
            unit_label,
            currency,
            notes,
        )

    async def update_rate(
        self, rid, cost_model, rate_microcents, unit_label, currency, notes
    ):
        await self.execute(
            Q.UPDATE_RATE, cost_model, rate_microcents, unit_label, currency, notes, rid
        )

    async def delete_rate(self, rid):
        await self.execute(Q.DELETE_RATE, rid)

    # ── Run Costs ────────────────────────────────────────────
    async def list_run_costs(self, run_id):
        return self._many(
            await self.find_all(Q.LIST_RUN_COSTS, run_id), WorkflowRunCost
        )

    async def list_workflow_costs(self, workflow_id, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_WORKFLOW_COSTS, workflow_id, limit, offset),
            WorkflowRunCost,
        )

    async def get_run_cost(self, cid):
        return self._one(WorkflowRunCost, await self.find_one(Q.GET_RUN_COST, cid))

    async def create_run_cost(
        self,
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
    ):
        await self.execute(
            Q.INSERT_RUN_COST,
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

    # ── Summary ──────────────────────────────────────────────
    async def get_cost_summary(self, workflow_id):
        return self._one(
            WorkflowCostSummary, await self.find_one(Q.GET_COST_SUMMARY, workflow_id)
        )

    async def list_cost_summaries(self, org_id):
        return self._many(
            await self.find_all(Q.LIST_COST_SUMMARIES, org_id), WorkflowCostSummary
        )

    async def upsert_cost_summary(
        self,
        workflow_id,
        org_id,
        total_runs_costed,
        total_cost,
        ad_spend,
        ai_cost,
        email_cost,
        last_run_cost,
        avg_run_cost,
        currency,
    ):
        await self.execute(
            Q.UPSERT_COST_SUMMARY,
            workflow_id,
            org_id,
            total_runs_costed,
            total_cost,
            ad_spend,
            ai_cost,
            email_cost,
            last_run_cost,
            avg_run_cost,
            currency,
        )

    # ── Monthly Rollup ───────────────────────────────────────
    async def get_monthly_rollup(self, org_id, year_month):
        return self._one(
            OrgCostMonthlyRollup,
            await self.find_one(Q.GET_MONTHLY_ROLLUP, org_id, year_month),
        )

    async def list_monthly_rollups(self, org_id, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_MONTHLY_ROLLUPS, org_id, limit, offset),
            OrgCostMonthlyRollup,
        )

    async def upsert_monthly_rollup(
        self,
        rid,
        org_id,
        year_month,
        workflow_runs,
        total_cost,
        ad_spend,
        ai_cost,
        email_cost,
        other_cost,
        budget_cap,
    ):
        await self.execute(
            Q.UPSERT_MONTHLY_ROLLUP,
            rid,
            org_id,
            year_month,
            workflow_runs,
            total_cost,
            ad_spend,
            ai_cost,
            email_cost,
            other_cost,
            budget_cap,
        )

    async def set_budget_cap(self, org_id, year_month, budget_cap_microcents):
        await self.execute(Q.SET_BUDGET_CAP, budget_cap_microcents, org_id, year_month)
