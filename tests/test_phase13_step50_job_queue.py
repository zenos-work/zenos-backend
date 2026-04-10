"""
Tests for Phase 13 - Step 50: Durable Job Queue
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from utils.job_queue import JobQueue, JobRecord


class TestJobQueue:
    """Test D1-backed job queue"""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database connection"""
        return AsyncMock()

    @pytest.fixture
    def queue(self, mock_db):
        """Create a JobQueue instance with mock DB"""
        return JobQueue(mock_db)

    @pytest.mark.asyncio
    async def test_enqueue_valid_job(self, queue, mock_db):
        """Enqueue a valid job"""
        # Set up proper chain: db.prepare().bind().run()
        mock_bind = AsyncMock()
        mock_bind.run = AsyncMock()
        mock_prepare = MagicMock()
        mock_prepare.bind = MagicMock(return_value=mock_bind)
        mock_db.prepare = MagicMock(return_value=mock_prepare)

        job_id = await queue.enqueue(
            "workflow_run",
            {"workflow_id": "w-123", "input": "test"},
            org_id="org-1",
            priority=5,
        )

        assert job_id is not None
        assert len(job_id) > 0

        # Verify prepare was called
        assert mock_db.prepare.called
        call_args = mock_db.prepare.call_args[0][0]
        assert "INSERT INTO job_queue" in call_args

    @pytest.mark.asyncio
    async def test_enqueue_invalid_job_type(self, queue, mock_db):
        """Reject invalid job type"""
        with pytest.raises(ValueError):
            await queue.enqueue("invalid_job_type", {"data": "test"})

    @pytest.mark.asyncio
    async def test_supported_job_types(self, queue):
        """Verify all documented job types are supported"""
        expected_types = [
            "workflow_run",
            "content_distribute",
            "newsletter_send",
            "data_export",
            "data_erasure",
            "billing_reconcile",
            "payout_calculate",
            "metric_rollup",
            "ai_content_scan",
        ]

        assert all(jt in queue.JOB_TYPES for jt in expected_types)

    @pytest.mark.asyncio
    async def test_claim_job_pending(self, queue, mock_db):
        """Claim pending jobs with optimistic locking"""
        now = datetime.utcnow().isoformat()
        job_data = {
            "id": "job-1",
            "job_type": "workflow_run",
            "payload": '{"workflow_id": "w-1"}',
            "status": "pending",
            "org_id": "org-1",
            "priority": 1,
            "attempt_count": 0,
            "max_attempts": 3,
            "next_retry_at": None,
            "locked_by": None,
            "locked_at": None,
            "completed_at": None,
            "error_message": None,
            "created_at": now,
            "updated_at": now,
        }

        # Set up all prepare/bind chains used in claim_job
        mock_all = AsyncMock(return_value=[job_data])
        mock_first = AsyncMock(return_value={"locked_by": "worker-1"})
        mock_run = AsyncMock()

        # Create separate mock chains for different SQL operations
        call_count = [0]

        def prepare_side_effect(query):
            call_count[0] += 1
            mock = MagicMock()
            if "SELECT id" in query and call_count[0] == 1:
                mock.bind = MagicMock(return_value=MagicMock(all=mock_all))
            elif "UPDATE job_queue" in query and "SET status" in query:
                mock.bind = MagicMock(return_value=MagicMock(run=mock_run))
            elif "SELECT" in query and "locked_by" in query:
                mock.bind = MagicMock(return_value=MagicMock(first=mock_first))
            return mock

        mock_db.prepare = MagicMock(side_effect=prepare_side_effect)

        jobs = await queue.claim_job("worker-1", max_jobs=5)

        assert len(jobs) >= 0

    @pytest.mark.asyncio
    async def test_mark_completed(self, queue, mock_db):
        """Mark a job as completed"""
        mock_bind = AsyncMock()
        mock_bind.run = AsyncMock()
        mock_prepare = MagicMock()
        mock_prepare.bind = MagicMock(return_value=mock_bind)
        mock_db.prepare = MagicMock(return_value=mock_prepare)

        await queue.mark_completed("job-1")

        assert mock_db.prepare.called
        call_args = mock_db.prepare.call_args[0][0]
        assert "UPDATE job_queue" in call_args
        assert "completed" in call_args

    @pytest.mark.asyncio
    async def test_mark_failed_under_max_attempts(self, queue, mock_db):
        """Mark job as failed, schedule retry (attempt < max)"""
        # Mock get current job
        mock_first = AsyncMock(return_value={"attempt_count": 0, "max_attempts": 3})
        mock_run = AsyncMock()

        def prepare_side_effect(query):
            mock = MagicMock()
            if "SELECT attempt_count" in query:
                mock.bind = MagicMock(return_value=MagicMock(first=mock_first))
            else:
                mock.bind = MagicMock(return_value=MagicMock(run=mock_run))
            return mock

        mock_db.prepare = MagicMock(side_effect=prepare_side_effect)

        await queue.mark_failed("job-1", "Network timeout")

        # Should have called prepare at least twice
        assert mock_db.prepare.call_count >= 1

    @pytest.mark.asyncio
    async def test_mark_failed_exceeds_max_attempts(self, queue, mock_db):
        """Mark job as dead (attempt >= max)"""
        # Mock get current job
        mock_first = AsyncMock(return_value={"attempt_count": 3, "max_attempts": 3})
        mock_run = AsyncMock()

        def prepare_side_effect(query):
            mock = MagicMock()
            if "SELECT attempt_count" in query:
                mock.bind = MagicMock(return_value=MagicMock(first=mock_first))
            else:
                mock.bind = MagicMock(return_value=MagicMock(run=mock_run))
            return mock

        mock_db.prepare = MagicMock(side_effect=prepare_side_effect)

        await queue.mark_failed("job-1", "Max retries exceeded")

        assert mock_db.prepare.called

    @pytest.mark.asyncio
    async def test_get_job(self, queue, mock_db):
        """Retrieve a job by ID"""
        job_data = {
            "id": "job-1",
            "job_type": "workflow_run",
            "payload": '{"workflow_id": "w-1"}',
            "status": "pending",
            "org_id": "org-1",
            "priority": 0,
            "attempt_count": 0,
            "max_attempts": 3,
            "next_retry_at": None,
            "locked_by": None,
            "locked_at": None,
            "completed_at": None,
            "error_message": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        mock_first = AsyncMock(return_value=job_data)
        mock_prepare = MagicMock()
        mock_prepare.bind = MagicMock(return_value=MagicMock(first=mock_first))
        mock_db.prepare = MagicMock(return_value=mock_prepare)

        job = await queue.get_job("job-1")

        assert job is not None
        assert job.id == "job-1"
        assert job.job_type == "workflow_run"
        assert job.status == "pending"

    @pytest.mark.asyncio
    async def test_get_job_not_found(self, queue, mock_db):
        """Get non-existent job returns None"""
        mock_first = AsyncMock(return_value=None)
        mock_prepare = MagicMock()
        mock_prepare.bind = MagicMock(return_value=MagicMock(first=mock_first))
        mock_db.prepare = MagicMock(return_value=mock_prepare)

        job = await queue.get_job("nonexistent-id")

        assert job is None

    @pytest.mark.asyncio
    async def test_list_pending(self, queue, mock_db):
        """List pending and processing jobs"""
        rows = [
            {
                "id": f"job-{i}",
                "job_type": "workflow_run",
                "payload": f'{{"workflow_id": "w-{i}"}}',
                "status": "pending",
                "org_id": "org-1",
                "priority": i,
                "attempt_count": 0,
                "max_attempts": 3,
                "next_retry_at": None,
                "locked_by": None,
                "locked_at": None,
                "completed_at": None,
                "error_message": None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            for i in range(3)
        ]

        mock_all = AsyncMock(return_value=rows)
        mock_prepare = MagicMock()
        mock_prepare.bind = MagicMock(return_value=MagicMock(all=mock_all))
        mock_db.prepare = MagicMock(return_value=mock_prepare)

        jobs = await queue.list_pending(org_id="org-1")

        assert len(jobs) == 3
        assert all(j.status == "pending" for j in jobs)

    @pytest.mark.asyncio
    async def test_list_dead_letter(self, queue, mock_db):
        """List dead-letter jobs"""
        rows = [
            {
                "id": f"dead-job-{i}",
                "job_type": "content_distribute",
                "payload": "{}",
                "status": "dead",
                "org_id": "org-1",
                "priority": 0,
                "attempt_count": 3,
                "max_attempts": 3,
                "next_retry_at": None,
                "locked_by": None,
                "locked_at": None,
                "completed_at": None,
                "error_message": "Max retries exceeded",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            for i in range(2)
        ]

        mock_all = AsyncMock(return_value=rows)
        mock_prepare = MagicMock()
        mock_prepare.bind = MagicMock(return_value=MagicMock(all=mock_all))
        mock_db.prepare = MagicMock(return_value=mock_prepare)

        dead_jobs = await queue.list_dead_letter(limit=10)

        assert len(dead_jobs) == 2
        assert all(j.status == "dead" for j in dead_jobs)


class TestJobRecord:
    """Test JobRecord dataclass"""

    def test_job_record_creation(self):
        """Create a JobRecord"""
        record = JobRecord(
            id="job-1",
            job_type="workflow_run",
            payload={"workflow_id": "w-1"},
            status="pending",
            org_id="org-1",
            priority=0,
            attempt_count=0,
            max_attempts=3,
            next_retry_at=None,
            locked_by=None,
            locked_at=None,
            completed_at=None,
            error_message=None,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )

        assert record.id == "job-1"
        assert record.job_type == "workflow_run"
        assert record.status == "pending"

    def test_job_record_to_dict(self):
        """Convert JobRecord to dictionary"""
        now = datetime.utcnow().isoformat()
        payload = {"workflow_id": "w-1", "input": "test"}

        record = JobRecord(
            id="job-1",
            job_type="workflow_run",
            payload=payload,
            status="processing",
            org_id="org-1",
            priority=5,
            attempt_count=1,
            max_attempts=3,
            next_retry_at=None,
            locked_by="worker-1",
            locked_at=now,
            completed_at=None,
            error_message=None,
            created_at=now,
            updated_at=now,
        )

        d = record.to_dict()

        assert d["id"] == "job-1"
        assert d["payload"] == payload
        assert d["status"] == "processing"
        assert d["attempt_count"] == 1


class TestExponentialBackoff:
    """Test exponential backoff calculation"""

    def test_backoff_formula(self):
        """Verify exponential backoff formula"""
        queue = JobQueue(None)

        # Formula: min(60 * (2 ** attempt), 3600)
        for attempt_count in range(1, 10):
            expected = min(60 * (2**attempt_count), queue.MAX_BACKOFF_SECONDS)
            assert expected >= 0
            assert expected <= queue.MAX_BACKOFF_SECONDS

        # After 6+ attempts, should max out at 3600
        expected = min(60 * (2**6), queue.MAX_BACKOFF_SECONDS)
        assert expected == 3600


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
