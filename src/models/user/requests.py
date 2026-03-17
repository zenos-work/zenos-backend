from dataclasses import dataclass
from typing import Optional
from models.base import BaseRequest
from models.common.enums import UserRole


@dataclass
class UpdateProfileRequest(BaseRequest):
    """Update user name and/or avatar. Both optional."""

    name: Optional[str] = None
    avatar_url: Optional[str] = None

    @classmethod
    def _validate(cls, data: dict) -> "UpdateProfileRequest":
        name = data.get("name")
        avatar_url = data.get("avatar_url")

        # At least one must be provided
        if name is None and avatar_url is None:
            raise ValueError("At least name or avatar_url must be provided")

        # Validate name if provided
        if name is not None:
            name = str(name).strip()
            if len(name) == 0:
                raise ValueError("Name cannot be empty")
            if len(name) > 100:
                raise ValueError("Name cannot be longer than 100 characters")

        return cls(name=name, avatar_url=avatar_url)


@dataclass
class UpdateRoleRequest(BaseRequest):
    role: str

    @classmethod
    def _validate(cls, data: dict) -> "UpdateRoleRequest":
        role = data.get("role")
        if not role:
            raise ValueError("Role is required")

        role = str(role).strip().upper()
        if role not in UserRole.ALL:
            raise ValueError(f"Invalid role: {role}. Must be one of {UserRole.ALL}")

        return cls(role=role)
