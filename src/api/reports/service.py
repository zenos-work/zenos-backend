from typing import Optional
from api.reports.repository import ReportRepository
from utils.helpers import new_id, paginate

VALID_REASONS = {
    "spam",
    "harassment",
    "hate_speech",
    "misinformation",
    "copyright",
    "nsfw",
    "self_harm",
    "impersonation",
    "off_topic",
    "other",
}

VALID_RESOURCE_TYPES = {
    "article",
    "comment",
    "user",
    "community_post",
    "marketplace_item",
}

VALID_STATUSES = {"pending", "under_review", "dismissed", "actioned", "escalated"}

VALID_ACTIONS = {
    "no_action",
    "content_removed",
    "content_hidden",
    "user_warned",
    "user_suspended",
    "user_banned",
    "escalated_to_legal",
    "other",
}


class ReportService:
    def __init__(self, env, ctx=None):
        self._repo = ReportRepository(env.DB, ctx)

    async def submit_report(
        self,
        reporter_id: str,
        resource_type: str,
        resource_id: str,
        reason: str,
        org_id: Optional[str] = None,
        detail_text: Optional[str] = None,
    ) -> str:
        if resource_type not in VALID_RESOURCE_TYPES:
            raise ValueError(f"Invalid resource_type: {resource_type}")
        if reason not in VALID_REASONS:
            raise ValueError(f"Invalid reason: {reason}")
        dup = await self._repo.check_duplicate(reporter_id, resource_type, resource_id)
        if dup:
            raise ValueError("You have already reported this resource")
        rid = new_id()
        await self._repo.create(
            rid, reporter_id, resource_type, resource_id, reason, org_id, detail_text
        )
        return rid

    async def list_reports(
        self, status: Optional[str] = None, page: int = 1, limit: int = 20
    ):
        _limit, offset = paginate(page, limit)
        if status:
            reports = await self._repo.find_by_status(status, _limit, offset)
            total = await self._repo.count_by_status(status)
        else:
            reports = await self._repo.find_all_reports(_limit, offset)
            total = await self._repo.count_all()
        return {
            "reports": [r.to_dict(scope="admin") for r in reports],
            "pagination": {
                "page": page,
                "limit": _limit,
                "total": total,
                "pages": (total + _limit - 1) // _limit if _limit else 0,
            },
        }

    async def review_report(
        self,
        report_id: str,
        reviewer_id: str,
        status: str,
        action_taken: Optional[str] = None,
        action_note: Optional[str] = None,
    ) -> dict:
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}")
        if action_taken and action_taken not in VALID_ACTIONS:
            raise ValueError(f"Invalid action_taken: {action_taken}")
        report = await self._repo.find_by_id(report_id)
        if not report:
            raise ValueError("Report not found")
        await self._repo.update_review(
            report_id, status, reviewer_id, action_taken, action_note
        )
        return {"id": report_id, "status": status}
