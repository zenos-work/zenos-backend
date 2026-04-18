"""
Tests for Phase 13 - Step 52: Workflow Promotion CI/CD
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from api.workflows.promotion import (
    PromotionService,
    WorkflowEnvironment,
    PromotionRequest,
    ENVIRONMENT_CONFIGS,
)


class TestWorkflowEnvironments:
    """Test environment definitions"""

    def test_dev_environment(self):
        """Dev environment allows unlimited runs, no metering"""
        env = ENVIRONMENT_CONFIGS[WorkflowEnvironment.DEV]
        assert env.allows_unlimited_runs is True
        assert env.cost_metering_enabled is False
        assert env.requires_approval is False

    def test_staging_environment(self):
        """Staging environment has 10 runs/day limit"""
        env = ENVIRONMENT_CONFIGS[WorkflowEnvironment.STAGING]
        assert env.allows_unlimited_runs is False
        assert env.max_runs_per_day == 10
        assert env.cost_metering_enabled is True

    def test_production_environment(self):
        """Production environment requires approval"""
        env = ENVIRONMENT_CONFIGS[WorkflowEnvironment.PRODUCTION]
        assert env.requires_approval is True
        assert env.cost_metering_enabled is True


class TestPromotionService:
    """Test workflow promotion service"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        return PromotionService(mock_db)

    @pytest.mark.asyncio
    async def test_request_promotion_dev_to_staging(self, service, mock_db):
        """Request promotion from dev to staging"""
        # Mock workflow retrieval
        mock_get_workflow = AsyncMock(
            return_value={
                "id": "w-1",
                "name": "Test Workflow",
                "nodes": [],
                "edges": [],
            }
        )
        service._get_workflow = mock_get_workflow

        # Mock DB prepare chain
        mock_bind = AsyncMock()
        mock_bind.run = AsyncMock()
        mock_prepare = MagicMock()
        mock_prepare.bind = MagicMock(return_value=mock_bind)
        mock_db.prepare = MagicMock(return_value=mock_prepare)

        request_id = await service.request_promotion(
            "w-1", "dev", "staging", "user-123", notes="Ready for testing"
        )

        assert request_id is not None
        assert len(request_id) > 0

    @pytest.mark.asyncio
    async def test_request_promotion_invalid_path(self, service, mock_db):
        """Reject invalid promotion path"""
        with pytest.raises(ValueError):
            await service.request_promotion(
                "w-1",
                "production",
                "dev",  # Can't go backwards
                "user-123",
            )

    @pytest.mark.asyncio
    async def test_approve_promotion(self, service, mock_db):
        """Approve and execute promotion"""
        # Mock methods
        mock_bind = AsyncMock()
        mock_bind.run = AsyncMock()
        mock_prepare = MagicMock()
        mock_prepare.bind = MagicMock(return_value=mock_bind)
        mock_db.prepare = MagicMock(return_value=mock_prepare)

        service._execute_promotion = AsyncMock(return_value=True)

        result = await service.approve_promotion(
            "promo-1", "approver-123", notes="Looks good!"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_reject_promotion(self, service, mock_db):
        """Reject a promotion request"""
        mock_bind = AsyncMock()
        mock_bind.run = AsyncMock()
        mock_prepare = MagicMock()
        mock_prepare.bind = MagicMock(return_value=mock_bind)
        mock_db.prepare = MagicMock(return_value=mock_prepare)

        result = await service.reject_promotion(
            "promo-1", "rejector-123", reason="Needs more testing"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_promotion_history(self, service, mock_db):
        """Retrieve promotion history for workflow"""
        rows = [
            {
                "id": f"promo-{i}",
                "workflow_id": "w-1",
                "from_env": "dev",
                "to_env": "staging",
                "status": "promoted",
                "requested_by": "user-123",
                "requested_at": datetime.now(timezone.utc).isoformat(),
                "approved_by": "approver-1",
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "promoted_at": datetime.now(timezone.utc).isoformat(),
                "notes": None,
                "test_results": None,
            }
            for i in range(3)
        ]

        mock_all = AsyncMock(return_value=rows)
        mock_prepare = MagicMock()
        mock_prepare.bind = MagicMock(return_value=MagicMock(all=mock_all))
        mock_db.prepare = MagicMock(return_value=mock_prepare)

        history = await service.get_promotion_history("w-1", limit=50)

        assert len(history) == 3
        assert all(isinstance(h, PromotionRequest) for h in history)

    @pytest.mark.asyncio
    async def test_get_environment_status(self, service, mock_db):
        """Get workflow status across environments"""

        # Mock workflow and run queries
        def prepare_side_effect(query):
            mock = MagicMock()
            if "SELECT id, environment" in query:
                mock.bind = MagicMock(
                    return_value=MagicMock(
                        first=AsyncMock(
                            return_value={
                                "id": "w-1",
                                "environment": "staging",
                                "updated_at": datetime.now(timezone.utc).isoformat(),
                            }
                        )
                    )
                )
            else:  # workflow_runs query
                mock.bind = MagicMock(
                    return_value=MagicMock(
                        first=AsyncMock(
                            return_value={
                                "run_count": 5,
                                "last_run": datetime.now(timezone.utc).isoformat(),
                            }
                        )
                    )
                )
            return mock

        mock_db.prepare = MagicMock(side_effect=prepare_side_effect)

        status = await service.get_environment_status("w-1")

        assert status is not None
        assert "dev" in status or "staging" in status or "production" in status


class TestPromotionRequest:
    """Test PromotionRequest data structure"""

    def test_create_promotion_request(self):
        """Create promotion request"""
        request = PromotionRequest(
            id="promo-1",
            workflow_id="w-1",
            from_env="dev",
            to_env="staging",
            status="pending",
            requested_by="user-123",
            requested_at=datetime.now(timezone.utc).isoformat(),
            approved_by=None,
            approved_at=None,
            promoted_at=None,
            notes="Testing",
            test_results=None,
        )

        assert request.id == "promo-1"
        assert request.status == "pending"
        assert request.approved_by is None

    def test_promotion_request_to_dict(self):
        """Convert promotion request to dict"""
        now = datetime.now(timezone.utc).isoformat()
        request = PromotionRequest(
            id="promo-1",
            workflow_id="w-1",
            from_env="dev",
            to_env="staging",
            status="promoted",
            requested_by="user-123",
            requested_at=now,
            approved_by="approver-1",
            approved_at=now,
            promoted_at=now,
            notes="All tests passed",
            test_results='{"passed": 10, "failed": 0}',
        )

        d = request.to_dict()
        assert d["id"] == "promo-1"
        assert d["status"] == "promoted"
        assert d["approved_by"] == "approver-1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
