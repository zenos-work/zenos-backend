"""Phase 10 Step 37 — Workflow cost models."""

from dataclasses import dataclass


@dataclass
class WorkflowNodeCostRate:
    id: str = ""
    org_id: str = ""
    node_type_id: str = ""
    cost_model: str = "per_execution"
    rate_microcents: int = 0
    unit_label: str = ""
    currency: str = "USD"
    notes: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id", "") or "",
            node_type_id=row.get("node_type_id", ""),
            cost_model=row.get("cost_model", "per_execution") or "per_execution",
            rate_microcents=int(row.get("rate_microcents", 0) or 0),
            unit_label=row.get("unit_label", "") or "",
            currency=row.get("currency", "USD") or "USD",
            notes=row.get("notes", "") or "",
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, scope="default"):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "node_type_id": self.node_type_id,
            "cost_model": self.cost_model,
            "rate_microcents": self.rate_microcents,
            "unit_label": self.unit_label,
            "currency": self.currency,
            "notes": self.notes,
            "created_at": self.created_at,
        }


@dataclass
class WorkflowRunCost:
    id: str = ""
    run_id: str = ""
    step_id: str = ""
    workflow_id: str = ""
    org_id: str = ""
    node_type_id: str = ""
    cost_model: str = ""
    units_consumed: float = 0.0
    unit_label: str = ""
    cost_microcents: int = 0
    cost_actual_microcents: int = 0
    currency: str = "USD"
    external_ref: str = ""
    notes: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            run_id=row.get("run_id", ""),
            step_id=row.get("step_id", "") or "",
            workflow_id=row.get("workflow_id", ""),
            org_id=row.get("org_id", "") or "",
            node_type_id=row.get("node_type_id", ""),
            cost_model=row.get("cost_model", ""),
            units_consumed=float(row.get("units_consumed", 0) or 0),
            unit_label=row.get("unit_label", "") or "",
            cost_microcents=int(row.get("cost_microcents", 0) or 0),
            cost_actual_microcents=int(row.get("cost_actual_microcents", 0) or 0),
            currency=row.get("currency", "USD") or "USD",
            external_ref=row.get("external_ref", "") or "",
            notes=row.get("notes", "") or "",
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, scope="default"):
        return {
            "id": self.id,
            "run_id": self.run_id,
            "step_id": self.step_id,
            "workflow_id": self.workflow_id,
            "org_id": self.org_id,
            "node_type_id": self.node_type_id,
            "cost_model": self.cost_model,
            "units_consumed": self.units_consumed,
            "unit_label": self.unit_label,
            "cost_microcents": self.cost_microcents,
            "cost_actual_microcents": self.cost_actual_microcents,
            "currency": self.currency,
            "external_ref": self.external_ref,
            "notes": self.notes,
            "created_at": self.created_at,
        }


@dataclass
class WorkflowCostSummary:
    workflow_id: str = ""
    org_id: str = ""
    total_runs_costed: int = 0
    total_cost_microcents: int = 0
    total_ad_spend_microcents: int = 0
    total_ai_cost_microcents: int = 0
    total_email_cost_microcents: int = 0
    last_run_cost_microcents: int = 0
    avg_run_cost_microcents: int = 0
    currency: str = "USD"
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            workflow_id=row.get("workflow_id", ""),
            org_id=row.get("org_id", "") or "",
            total_runs_costed=int(row.get("total_runs_costed", 0) or 0),
            total_cost_microcents=int(row.get("total_cost_microcents", 0) or 0),
            total_ad_spend_microcents=int(row.get("total_ad_spend_microcents", 0) or 0),
            total_ai_cost_microcents=int(row.get("total_ai_cost_microcents", 0) or 0),
            total_email_cost_microcents=int(
                row.get("total_email_cost_microcents", 0) or 0
            ),
            last_run_cost_microcents=int(row.get("last_run_cost_microcents", 0) or 0),
            avg_run_cost_microcents=int(row.get("avg_run_cost_microcents", 0) or 0),
            currency=row.get("currency", "USD") or "USD",
            updated_at=row.get("updated_at", "") or "",
        )

    def to_dict(self, scope="default"):
        return {
            "workflow_id": self.workflow_id,
            "org_id": self.org_id,
            "total_runs_costed": self.total_runs_costed,
            "total_cost_microcents": self.total_cost_microcents,
            "total_ad_spend_microcents": self.total_ad_spend_microcents,
            "total_ai_cost_microcents": self.total_ai_cost_microcents,
            "total_email_cost_microcents": self.total_email_cost_microcents,
            "last_run_cost_microcents": self.last_run_cost_microcents,
            "avg_run_cost_microcents": self.avg_run_cost_microcents,
            "currency": self.currency,
            "updated_at": self.updated_at,
        }


@dataclass
class OrgCostMonthlyRollup:
    id: str = ""
    org_id: str = ""
    year_month: str = ""
    workflow_runs: int = 0
    total_cost_microcents: int = 0
    ad_spend_microcents: int = 0
    ai_cost_microcents: int = 0
    email_cost_microcents: int = 0
    other_cost_microcents: int = 0
    budget_cap_microcents: int = 0
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id", ""),
            year_month=row.get("year_month", ""),
            workflow_runs=int(row.get("workflow_runs", 0) or 0),
            total_cost_microcents=int(row.get("total_cost_microcents", 0) or 0),
            ad_spend_microcents=int(row.get("ad_spend_microcents", 0) or 0),
            ai_cost_microcents=int(row.get("ai_cost_microcents", 0) or 0),
            email_cost_microcents=int(row.get("email_cost_microcents", 0) or 0),
            other_cost_microcents=int(row.get("other_cost_microcents", 0) or 0),
            budget_cap_microcents=int(row.get("budget_cap_microcents", 0) or 0),
            updated_at=row.get("updated_at", "") or "",
        )

    def to_dict(self, scope="default"):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "year_month": self.year_month,
            "workflow_runs": self.workflow_runs,
            "total_cost_microcents": self.total_cost_microcents,
            "ad_spend_microcents": self.ad_spend_microcents,
            "ai_cost_microcents": self.ai_cost_microcents,
            "email_cost_microcents": self.email_cost_microcents,
            "other_cost_microcents": self.other_cost_microcents,
            "budget_cap_microcents": self.budget_cap_microcents,
            "updated_at": self.updated_at,
        }
