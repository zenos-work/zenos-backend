from typing import Optional, List
from db.repository import BaseRepository
from api.reports import queries as Q
from models.report.model import ContentReport
from models.base import row_get


class ReportRepository(BaseRepository):
    async def create(
        self,
        report_id: str,
        reporter_id: str,
        resource_type: str,
        resource_id: str,
        reason: str,
        org_id: Optional[str] = None,
        detail_text: Optional[str] = None,
    ) -> None:
        await self.execute(
            Q.INSERT_REPORT,
            report_id,
            reporter_id,
            org_id or "",
            resource_type,
            resource_id,
            reason,
            detail_text or "",
        )

    async def find_by_id(self, report_id: str) -> Optional[ContentReport]:
        row = await self.find_one(Q.SELECT_BY_ID, report_id)
        return self.map_one(row, ContentReport)

    async def find_all_reports(self, limit: int, offset: int) -> List[ContentReport]:
        rows = await self.find_all(Q.SELECT_ALL, limit, offset)
        return self.map_many(rows, ContentReport)

    async def find_by_status(
        self, status: str, limit: int, offset: int
    ) -> List[ContentReport]:
        rows = await self.find_all(Q.SELECT_BY_STATUS, status, limit, offset)
        return self.map_many(rows, ContentReport)

    async def count_all(self) -> int:
        row = await self.find_one(Q.COUNT_ALL)
        return row_get(row, "c", 0)

    async def count_by_status(self, status: str) -> int:
        row = await self.find_one(Q.COUNT_BY_STATUS, status)
        return row_get(row, "c", 0)

    async def update_review(
        self,
        report_id: str,
        status: str,
        reviewed_by: str,
        action_taken: Optional[str] = None,
        action_note: Optional[str] = None,
    ) -> None:
        await self.execute(
            Q.UPDATE_REVIEW,
            status,
            reviewed_by,
            action_taken or "",
            action_note or "",
            report_id,
        )

    async def check_duplicate(
        self, reporter_id: str, resource_type: str, resource_id: str
    ) -> bool:
        row = await self.find_one(
            Q.CHECK_DUPLICATE, reporter_id, resource_type, resource_id
        )
        return row is not None
