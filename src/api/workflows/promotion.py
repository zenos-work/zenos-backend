"""
Phase 13 - Step 52: Workflow dev→prod promotion CI/CD
Internal environment promotion system within OmniFlow.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, List
from enum import Enum
from datetime import datetime
import json


class WorkflowEnvironment(str, Enum):
    """Workflow execution environments"""

    DEV = "dev"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class EnvironmentConfig:
    """Configuration for each environment"""

    name: str
    description: str
    allows_unlimited_runs: bool
    cost_metering_enabled: bool
    max_runs_per_day: Optional[int]
    requires_approval: bool
    auto_promote_on_success: bool


# Environment definitions
ENVIRONMENT_CONFIGS = {
    WorkflowEnvironment.DEV: EnvironmentConfig(
        name="dev",
        description="Build & test with mock data",
        allows_unlimited_runs=True,
        cost_metering_enabled=False,
        max_runs_per_day=None,
        requires_approval=False,
        auto_promote_on_success=False,
    ),
    WorkflowEnvironment.STAGING: EnvironmentConfig(
        name="staging",
        description="Integration testing with real connectors",
        allows_unlimited_runs=False,
        cost_metering_enabled=True,
        max_runs_per_day=10,
        requires_approval=False,
        auto_promote_on_success=False,
    ),
    WorkflowEnvironment.PRODUCTION: EnvironmentConfig(
        name="production",
        description="Live execution",
        allows_unlimited_runs=False,
        cost_metering_enabled=True,
        max_runs_per_day=None,
        requires_approval=True,
        auto_promote_on_success=False,
    ),
}


@dataclass
class PromotionRequest:
    """A workflow environment promotion request"""

    id: str
    workflow_id: str
    from_env: str
    to_env: str
    status: str  # pending, approved, rejected, promoted
    requested_by: str
    requested_at: str
    approved_by: Optional[str]
    approved_at: Optional[str]
    promoted_at: Optional[str]
    notes: Optional[str]
    test_results: Optional[str]  # JSON with test run metrics

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "from_env": self.from_env,
            "to_env": self.to_env,
            "status": self.status,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "promoted_at": self.promoted_at,
            "notes": self.notes,
            "test_results": self.test_results,
        }


@dataclass
class WorkflowVersion:
    """Immutable snapshot of a workflow at promotion time"""

    id: str
    workflow_id: str
    environment: str
    version_number: int
    workflow_data: Dict[str, Any]  # Full workflow definition
    promoted_from_version: Optional[str]
    created_at: str
    created_by: str


class PromotionService:
    """Manages workflow promotions between environments"""

    def __init__(self, db: Any):
        """Initialize with database connection"""
        self.db = db

    async def request_promotion(
        self,
        workflow_id: str,
        from_env: str,
        to_env: str,
        requested_by: str,
        notes: Optional[str] = None,
    ) -> str:
        """
        Request a promotion from one environment to another.

        Args:
            workflow_id: ID of workflow to promote
            from_env: Source environment (dev, staging, production)
            to_env: Target environment
            requested_by: User ID requesting promotion
            notes: Optional notes about the promotion

        Returns:
            Promotion request ID
        """
        # Validate environments
        if from_env not in [e.value for e in WorkflowEnvironment]:
            raise ValueError(f"Unknown source environment: {from_env}")
        if to_env not in [e.value for e in WorkflowEnvironment]:
            raise ValueError(f"Unknown target environment: {to_env}")

        # Validate promotion path (must be sequential)
        valid_paths = [
            ("dev", "staging"),
            ("staging", "production"),
        ]

        if (from_env, to_env) not in valid_paths:
            raise ValueError(f"Cannot promote from {from_env} to {to_env}")

        # Get current workflow version
        workflow = await self._get_workflow(workflow_id, from_env)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        # Create promotion request
        request_id = self._generate_id()

        query = """
            INSERT INTO workflow_promotions (
                id, workflow_id, from_env, to_env, status,
                requested_by, requested_at, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        now = datetime.utcnow().isoformat()
        try:
            await (
                self.db.prepare(query)
                .bind(
                    request_id,
                    workflow_id,
                    from_env,
                    to_env,
                    "pending",
                    requested_by,
                    now,
                    notes,
                    now,
                )
                .run()
            )

            return request_id
        except Exception as e:
            raise RuntimeError(f"Failed to create promotion request: {str(e)}")

    async def approve_promotion(
        self,
        promotion_id: str,
        approved_by: str,
        notes: Optional[str] = None,
    ) -> bool:
        """Approve a promotion request"""
        now = datetime.utcnow().isoformat()

        query = """
            UPDATE workflow_promotions
            SET status = 'approved', approved_by = ?, approved_at = ?, notes = ?
            WHERE id = ? AND status = 'pending'
        """

        try:
            await (
                self.db.prepare(query).bind(approved_by, now, notes, promotion_id).run()
            )

            # Execute the promotion
            return await self._execute_promotion(promotion_id)
        except Exception as e:
            raise RuntimeError(f"Failed to approve promotion: {str(e)}")

    async def reject_promotion(
        self,
        promotion_id: str,
        rejected_by: str,
        reason: str,
    ) -> bool:
        """Reject a promotion request"""

        query = """
            UPDATE workflow_promotions
            SET status = 'rejected', notes = ?
            WHERE id = ? AND status = 'pending'
        """

        try:
            await self.db.prepare(query).bind(reason, promotion_id).run()

            return True
        except Exception as e:
            raise RuntimeError(f"Failed to reject promotion: {str(e)}")

    async def _execute_promotion(self, promotion_id: str) -> bool:
        """Execute the actual promotion (copy workflow to target env)"""
        try:
            # Get promotion request details
            promo_query = "SELECT * FROM workflow_promotions WHERE id = ?"
            promo = await self.db.prepare(promo_query).bind(promotion_id).first()

            if not promo:
                raise ValueError(f"Promotion not found: {promotion_id}")

            # Get current workflow from source environment
            workflow = await self._get_workflow(promo["workflow_id"], promo["from_env"])

            # Create version snapshot
            await self._create_workflow_version(
                promo["workflow_id"],
                promo["to_env"],
                workflow,
                requested_by=promo["requested_by"],
            )

            # Update workflow to new environment
            update_query = """
                UPDATE workflows
                SET environment = ?, updated_at = datetime('now')
                WHERE id = ?
            """

            await (
                self.db.prepare(update_query)
                .bind(promo["to_env"], promo["workflow_id"])
                .run()
            )

            # Mark promotion as complete
            promote_query = """
                UPDATE workflow_promotions
                SET status = 'promoted', promoted_at = datetime('now')
                WHERE id = ?
            """

            await self.db.prepare(promote_query).bind(promotion_id).run()

            return True
        except Exception as e:
            raise RuntimeError(f"Failed to execute promotion: {str(e)}")

    async def rollback(
        self,
        workflow_id: str,
        rollback_to_version_id: str,
    ) -> bool:
        """Rollback production workflow to previous version"""
        try:
            # Get target version
            version_query = (
                "SELECT * FROM workflow_versions WHERE id = ? AND workflow_id = ?"
            )
            version = (
                await self.db.prepare(version_query)
                .bind(rollback_to_version_id, workflow_id)
                .first()
            )

            if not version:
                raise ValueError("Version not found")

            # Verify target is production
            if version["environment"] != "production":
                raise ValueError("Can only rollback to production versions")

            # Restore workflow from version
            workflow_data = json.loads(version["workflow_data"])

            update_query = """
                UPDATE workflows
                SET nodes = ?, edges = ?, updated_at = datetime('now')
                WHERE id = ?
            """

            await (
                self.db.prepare(update_query)
                .bind(
                    json.dumps(workflow_data.get("nodes", [])),
                    json.dumps(workflow_data.get("edges", [])),
                    workflow_id,
                )
                .run()
            )

            return True
        except Exception as e:
            raise RuntimeError(f"Failed to rollback: {str(e)}")

    async def get_promotion_history(
        self,
        workflow_id: str,
        limit: int = 50,
    ) -> List[PromotionRequest]:
        """Get promotion history for a workflow"""
        query = """
            SELECT id, workflow_id, from_env, to_env, status,
                   requested_by, requested_at, approved_by, approved_at,
                   promoted_at, notes, test_results
            FROM workflow_promotions
            WHERE workflow_id = ?
            ORDER BY requested_at DESC
            LIMIT ?
        """

        try:
            rows = await self.db.prepare(query).bind(workflow_id, limit).all()

            return [
                PromotionRequest(
                    id=row["id"],
                    workflow_id=row["workflow_id"],
                    from_env=row["from_env"],
                    to_env=row["to_env"],
                    status=row["status"],
                    requested_by=row["requested_by"],
                    requested_at=row["requested_at"],
                    approved_by=row.get("approved_by"),
                    approved_at=row.get("approved_at"),
                    promoted_at=row.get("promoted_at"),
                    notes=row.get("notes"),
                    test_results=row.get("test_results"),
                )
                for row in rows
            ]
        except Exception as e:
            raise RuntimeError(f"Failed to get promotion history: {str(e)}")

    async def get_environment_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of workflow in all environments"""
        try:
            query = "SELECT id, environment, updated_at FROM workflows WHERE id = ?"
            workflow = await self.db.prepare(query).bind(workflow_id).first()

            if not workflow:
                return {}

            status = {}
            for env in [
                WorkflowEnvironment.DEV,
                WorkflowEnvironment.STAGING,
                WorkflowEnvironment.PRODUCTION,
            ]:
                run_query = """
                    SELECT COUNT(*) as run_count, MAX(created_at) as last_run
                    FROM workflow_runs
                    WHERE workflow_id = ? AND environment = ?
                """

                run_stats = (
                    await self.db.prepare(run_query)
                    .bind(workflow_id, env.value)
                    .first()
                )

                status[env.value] = {
                    "last_updated": workflow.get("updated_at")
                    if workflow.get("environment") == env.value
                    else None,
                    "total_runs": run_stats.get("run_count", 0) if run_stats else 0,
                    "last_run_at": run_stats.get("last_run") if run_stats else None,
                    "is_current": workflow.get("environment") == env.value,
                }

            return status
        except Exception as e:
            raise RuntimeError(f"Failed to get environment status: {str(e)}")

    async def _get_workflow(
        self, workflow_id: str, environment: str
    ) -> Optional[Dict[str, Any]]:
        """Get workflow definition for specific environment"""
        query = """
            SELECT id, name, nodes, edges, environment FROM workflows
            WHERE id = ? AND environment = ?
        """

        try:
            row = await self.db.prepare(query).bind(workflow_id, environment).first()

            if not row:
                return None

            return {
                "id": row["id"],
                "name": row["name"],
                "nodes": json.loads(row.get("nodes", "[]")),
                "edges": json.loads(row.get("edges", "[]")),
                "environment": row["environment"],
            }
        except Exception as e:
            print(f"Failed to get workflow: {str(e)}")
            return None

    async def _create_workflow_version(
        self,
        workflow_id: str,
        environment: str,
        workflow_data: Dict[str, Any],
        requested_by: str,
    ) -> Optional[str]:
        """Create immutable workflow version snapshot"""
        try:
            version_id = self._generate_id()
            now = datetime.utcnow().isoformat()

            query = """
                INSERT INTO workflow_versions (
                    id, workflow_id, environment, version_number,
                    workflow_data, promoted_from_version, created_at, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            # Get next version number
            version_query = """
                SELECT MAX(version_number) as max_version FROM workflow_versions
                WHERE workflow_id = ? AND environment = ?
            """

            result = (
                await self.db.prepare(version_query)
                .bind(workflow_id, environment)
                .first()
            )

            next_version = (result.get("max_version", 0) if result else 0) + 1

            await (
                self.db.prepare(query)
                .bind(
                    version_id,
                    workflow_id,
                    environment,
                    next_version,
                    json.dumps(workflow_data),
                    None,  # promoted_from_version
                    now,
                    requested_by,
                )
                .run()
            )

            return version_id
        except Exception as e:
            print(f"Failed to create workflow version: {str(e)}")
            return None

    @staticmethod
    def _generate_id() -> str:
        """Generate a unique ID"""
        import uuid

        return str(uuid.uuid4())
