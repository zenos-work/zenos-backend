from dataclasses import dataclass
from typing import Optional
from models.base import BaseModel, row_get
from models.common.enums import Scope

_PUBLIC_FIELDS = {"id", "name", "role", "avatar_url", "created_at"}
_PRIVATE_FIELDS = _PUBLIC_FIELDS | {
    "email",
    "is_active",
    "updated_at",
    "terms_accepted_at",
}
_ADMIN_FIELDS = _PRIVATE_FIELDS | {"google_id"}

_SCOPE_MAP = {
    Scope.PUBLIC: _PUBLIC_FIELDS,
    Scope.PRIVATE: _PRIVATE_FIELDS,
    Scope.ADMIN: _ADMIN_FIELDS,
}


@dataclass
class User(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: int
    created_at: str
    updated_at: str
    avatar_url: Optional[str] = None
    google_id: Optional[str] = None
    terms_accepted_at: Optional[str] = None

    def to_dict(self, scope: str = Scope.PUBLIC) -> dict:
        allowed = _SCOPE_MAP.get(scope, _PUBLIC_FIELDS)
        return {
            k: v
            for k, v in {
                "id": self.id,
                "email": self.email,
                "name": self.name,
                "role": self.role,
                "is_active": self.is_active,
                "avatar_url": self.avatar_url,
                "google_id": self.google_id,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "terms_accepted_at": self.terms_accepted_at,
            }.items()
            if k in allowed and v is not None
        }

    @classmethod
    def from_row(cls, row) -> "User":
        return cls(
            id=row_get(row, "id"),
            email=row_get(row, "email", ""),
            name=row_get(row, "name", ""),
            role=row_get(row, "role", "READER"),
            is_active=row_get(row, "is_active", 1),
            created_at=row_get(row, "created_at", ""),
            updated_at=row_get(row, "updated_at", ""),
            avatar_url=row_get(row, "avatar_url"),
            google_id=row_get(row, "google_id"),
            terms_accepted_at=row_get(row, "terms_accepted_at"),
        )
