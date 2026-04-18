from dataclasses import dataclass
from typing import Optional
from models.base import BaseModel, row_get


@dataclass
class ContentReport(BaseModel):
    id: str
    reporter_id: str
    resource_type: str
    resource_id: str
    reason: str
    status: str
    created_at: str
    updated_at: str
    org_id: Optional[str] = None
    detail_text: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    action_taken: Optional[str] = None
    action_note: Optional[str] = None

    def to_dict(self, scope: str = "public") -> dict:
        d = {
            "id": self.id,
            "reporter_id": self.reporter_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "reason": self.reason,
            "status": self.status,
            "detail_text": self.detail_text,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if scope == "admin":
            d["org_id"] = self.org_id
            d["reviewed_by"] = self.reviewed_by
            d["reviewed_at"] = self.reviewed_at
            d["action_taken"] = self.action_taken
            d["action_note"] = self.action_note
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_row(cls, row) -> "ContentReport":
        return cls(
            id=row_get(row, "id"),
            reporter_id=row_get(row, "reporter_id"),
            resource_type=row_get(row, "resource_type"),
            resource_id=row_get(row, "resource_id"),
            reason=row_get(row, "reason"),
            status=row_get(row, "status", "pending"),
            created_at=row_get(row, "created_at", ""),
            updated_at=row_get(row, "updated_at", ""),
            org_id=row_get(row, "org_id"),
            detail_text=row_get(row, "detail_text"),
            reviewed_by=row_get(row, "reviewed_by"),
            reviewed_at=row_get(row, "reviewed_at"),
            action_taken=row_get(row, "action_taken"),
            action_note=row_get(row, "action_note"),
        )
