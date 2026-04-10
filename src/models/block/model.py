from dataclasses import dataclass
from typing import Optional
from models.base import BaseModel, row_get


@dataclass
class UserBlock(BaseModel):
    blocker_id: str
    blocked_id: str
    block_type: str
    created_at: str
    reason: Optional[str] = None

    def to_dict(self, scope: str = "public") -> dict:
        d = {
            "blocker_id": self.blocker_id,
            "blocked_id": self.blocked_id,
            "block_type": self.block_type,
            "reason": self.reason,
            "created_at": self.created_at,
        }
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_row(cls, row) -> "UserBlock":
        return cls(
            blocker_id=row_get(row, "blocker_id"),
            blocked_id=row_get(row, "blocked_id"),
            block_type=row_get(row, "block_type", "block"),
            created_at=row_get(row, "created_at", ""),
            reason=row_get(row, "reason"),
        )
