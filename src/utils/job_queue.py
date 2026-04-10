"""
Phase 13 - Step 50: D1-backed Durable Execution Queue
At-least-once delivery via D1 polling without Cloudflare Queues (free tier compatible).
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
import json
import uuid


@dataclass
class JobRecord:
    """A job in the queue"""

    id: str
    job_type: str
    payload: Dict[str, Any]
    status: str  # pending, processing, completed, failed, dead
    org_id: Optional[str]
    priority: int
    attempt_count: int
    max_attempts: int
    next_retry_at: Optional[str]
    locked_by: Optional[str]
    locked_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "job_type": self.job_type,
            "payload": self.payload
            if isinstance(self.payload, dict)
            else json.loads(self.payload),
            "status": self.status,
            "org_id": self.org_id,
            "priority": self.priority,
            "attempt_count": self.attempt_count,
            "max_attempts": self.max_attempts,
            "next_retry_at": self.next_retry_at,
            "locked_by": self.locked_by,
            "locked_at": self.locked_at,
            "completed_at": self.completed_at,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class JobQueue:
    """
    D1-backed job queue with optimistic locking.

    Guarantees: At-least-once delivery.
    Idempotency is caller's responsibility via idempotency_key in payload.
    """

    # Define supported job types
    JOB_TYPES = [
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

    # Default max attempts per job
    DEFAULT_MAX_ATTEMPTS = 3

    # Exponential backoff: min(60 * (2 ** attempt), 3600) seconds
    MAX_BACKOFF_SECONDS = 3600  # 1 hour

    def __init__(self, db: Any):
        """Initialize with D1 database connection"""
        self.db = db

    async def enqueue(
        self,
        job_type: str,
        payload: Dict[str, Any],
        org_id: Optional[str] = None,
        priority: int = 0,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        idempotency_key: Optional[str] = None,
    ) -> str:
        """
        Enqueue a new job.

        Args:
            job_type: Type of job (must be in JOB_TYPES)
            payload: Job payload (should include idempotency_key for idempotent jobs)
            org_id: Organization ID (for multi-tenant isolation)
            priority: Priority (higher = sooner, default 0)
            max_attempts: Maximum retry attempts
            idempotency_key: Idempotency key (optional, for duplicate detection)

        Returns:
            Job ID
        """
        if job_type not in self.JOB_TYPES:
            raise ValueError(f"Unknown job type: {job_type}")

        job_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        query = """
            INSERT INTO job_queue (
                id, job_type, payload, status, org_id, priority,
                attempt_count, max_attempts, next_retry_at,
                locked_by, locked_at, completed_at, error_message,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        try:
            await (
                self.db.prepare(query)
                .bind(
                    job_id,
                    job_type,
                    json.dumps(payload),
                    "pending",
                    org_id,
                    priority,
                    0,  # attempt_count
                    max_attempts,
                    None,  # next_retry_at
                    None,  # locked_by
                    None,  # locked_at
                    None,  # completed_at
                    None,  # error_message
                    now,
                    now,
                )
                .run()
            )

            return job_id
        except Exception as e:
            raise RuntimeError(f"Failed to enqueue job: {str(e)}")

    async def claim_job(self, worker_id: str, max_jobs: int = 5) -> List[JobRecord]:
        """
        Claim up to max_jobs pending jobs using optimistic locking.

        This is called by the job processor cron (every 1 minute).

        Args:
            worker_id: Unique identifier for this worker/cron invocation
            max_jobs: Maximum jobs to claim per run

        Returns:
            List of claimed jobs (locked for processing)
        """
        now = datetime.utcnow().isoformat()

        # Find pending jobs (sorted by priority, then created_at)
        fetch_query = """
            SELECT id, job_type, payload, status, org_id, priority,
                   attempt_count, max_attempts, next_retry_at,
                   locked_by, locked_at, completed_at, error_message,
                   created_at, updated_at
            FROM job_queue
            WHERE status = 'pending'
              AND (next_retry_at IS NULL OR next_retry_at <= ?)
            ORDER BY priority DESC, created_at ASC
            LIMIT ?
        """

        try:
            results = await self.db.prepare(fetch_query).bind(now, max_jobs).all()

            jobs = []
            for row in results:
                # Try to lock this job
                lock_query = """
                    UPDATE job_queue
                    SET status = 'processing', locked_by = ?, locked_at = ?
                    WHERE id = ?
                      AND status = 'pending'
                """

                await self.db.prepare(lock_query).bind(worker_id, now, row["id"]).run()

                # Verify lock was acquired
                verify_query = "SELECT * FROM job_queue WHERE id = ? AND locked_by = ?"
                verify_result = (
                    await self.db.prepare(verify_query)
                    .bind(row["id"], worker_id)
                    .first()
                )

                if verify_result:
                    jobs.append(
                        JobRecord(
                            id=row["id"],
                            job_type=row["job_type"],
                            payload=json.loads(row["payload"])
                            if isinstance(row["payload"], str)
                            else row["payload"],
                            status=row["status"],
                            org_id=row["org_id"],
                            priority=row["priority"],
                            attempt_count=row["attempt_count"],
                            max_attempts=row["max_attempts"],
                            next_retry_at=row["next_retry_at"],
                            locked_by=row["locked_by"],
                            locked_at=row["locked_at"],
                            completed_at=row["completed_at"],
                            error_message=row["error_message"],
                            created_at=row["created_at"],
                            updated_at=row["updated_at"],
                        )
                    )

            return jobs
        except Exception as e:
            raise RuntimeError(f"Failed to claim jobs: {str(e)}")

    async def mark_completed(self, job_id: str) -> None:
        """Mark a job as successfully completed"""
        now = datetime.utcnow().isoformat()

        query = """
            UPDATE job_queue
            SET status = 'completed', completed_at = ?, updated_at = ?
            WHERE id = ?
        """

        try:
            await self.db.prepare(query).bind(now, now, job_id).run()
        except Exception as e:
            raise RuntimeError(f"Failed to mark job completed: {str(e)}")

    async def mark_failed(self, job_id: str, error_message: str) -> None:
        """
        Mark a job as failed with exponential backoff retry.

        After max_attempts, moves to 'dead' status.
        """
        now = datetime.utcnow().isoformat()

        # Get current job state
        query = "SELECT attempt_count, max_attempts FROM job_queue WHERE id = ?"
        job = await self.db.prepare(query).bind(job_id).first()

        if not job:
            raise RuntimeError(f"Job not found: {job_id}")

        next_attempt = job["attempt_count"] + 1

        if next_attempt >= job["max_attempts"]:
            # Max retries exceeded, move to dead
            update_query = """
                UPDATE job_queue
                SET status = 'dead', error_message = ?, attempt_count = ?,
                    updated_at = ?
                WHERE id = ?
            """
            await (
                self.db.prepare(update_query)
                .bind(error_message, next_attempt, now, job_id)
                .run()
            )
        else:
            # Schedule retry with exponential backoff
            backoff_seconds = min(60 * (2**next_attempt), self.MAX_BACKOFF_SECONDS)
            next_retry_at = (
                datetime.utcnow() + timedelta(seconds=backoff_seconds)
            ).isoformat()

            update_query = """
                UPDATE job_queue
                SET status = 'pending', error_message = ?, attempt_count = ?,
                    next_retry_at = ?, locked_by = NULL, locked_at = NULL,
                    updated_at = ?
                WHERE id = ?
            """

            await (
                self.db.prepare(update_query)
                .bind(error_message, next_attempt, next_retry_at, now, job_id)
                .run()
            )

    async def get_job(self, job_id: str) -> Optional[JobRecord]:
        """Get a specific job by ID"""
        query = """
            SELECT id, job_type, payload, status, org_id, priority,
                   attempt_count, max_attempts, next_retry_at,
                   locked_by, locked_at, completed_at, error_message,
                   created_at, updated_at
            FROM job_queue
            WHERE id = ?
        """

        try:
            row = await self.db.prepare(query).bind(job_id).first()

            if not row:
                return None

            return JobRecord(
                id=row["id"],
                job_type=row["job_type"],
                payload=json.loads(row["payload"])
                if isinstance(row["payload"], str)
                else row["payload"],
                status=row["status"],
                org_id=row["org_id"],
                priority=row["priority"],
                attempt_count=row["attempt_count"],
                max_attempts=row["max_attempts"],
                next_retry_at=row["next_retry_at"],
                locked_by=row["locked_by"],
                locked_at=row["locked_at"],
                completed_at=row["completed_at"],
                error_message=row["error_message"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
        except Exception as e:
            raise RuntimeError(f"Failed to get job: {str(e)}")

    async def list_pending(
        self, org_id: Optional[str] = None, limit: int = 100
    ) -> List[JobRecord]:
        """List pending jobs (for monitoring)"""
        query = """
            SELECT id, job_type, payload, status, org_id, priority,
                   attempt_count, max_attempts, next_retry_at,
                   locked_by, locked_at, completed_at, error_message,
                   created_at, updated_at
            FROM job_queue
            WHERE status IN ('pending', 'processing')
        """

        params = []

        if org_id:
            query += " AND org_id = ?"
            params.append(org_id)

        query += " ORDER BY priority DESC, created_at ASC LIMIT ?"
        params.append(limit)

        try:
            rows = await self.db.prepare(query).bind(*params).all()

            return [
                JobRecord(
                    id=row["id"],
                    job_type=row["job_type"],
                    payload=json.loads(row["payload"])
                    if isinstance(row["payload"], str)
                    else row["payload"],
                    status=row["status"],
                    org_id=row["org_id"],
                    priority=row["priority"],
                    attempt_count=row["attempt_count"],
                    max_attempts=row["max_attempts"],
                    next_retry_at=row["next_retry_at"],
                    locked_by=row["locked_by"],
                    locked_at=row["locked_at"],
                    completed_at=row["completed_at"],
                    error_message=row["error_message"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]
        except Exception as e:
            raise RuntimeError(f"Failed to list jobs: {str(e)}")

    async def list_dead_letter(self, limit: int = 100) -> List[JobRecord]:
        """List dead-letter jobs (max attempts exceeded)"""
        query = """
            SELECT id, job_type, payload, status, org_id, priority,
                   attempt_count, max_attempts, next_retry_at,
                   locked_by, locked_at, completed_at, error_message,
                   created_at, updated_at
            FROM job_queue
            WHERE status = 'dead'
            ORDER BY updated_at DESC
            LIMIT ?
        """

        try:
            rows = await self.db.prepare(query).bind(limit).all()

            return [
                JobRecord(
                    id=row["id"],
                    job_type=row["job_type"],
                    payload=json.loads(row["payload"])
                    if isinstance(row["payload"], str)
                    else row["payload"],
                    status=row["status"],
                    org_id=row["org_id"],
                    priority=row["priority"],
                    attempt_count=row["attempt_count"],
                    max_attempts=row["max_attempts"],
                    next_retry_at=row["next_retry_at"],
                    locked_by=row["locked_by"],
                    locked_at=row["locked_at"],
                    completed_at=row["completed_at"],
                    error_message=row["error_message"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]
        except Exception as e:
            raise RuntimeError(f"Failed to list dead-letter jobs: {str(e)}")
