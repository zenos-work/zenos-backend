import re
from dataclasses import dataclass
from typing import Optional
from models.base import BaseRequest
from models.common.enums import UserRole

_HANDLE_RE = re.compile(r"^[a-zA-Z0-9_-]{3,40}$")


@dataclass
class UpdateProfileRequest(BaseRequest):
    """Update user profile fields. All optional."""

    name: Optional[str] = None
    avatar_url: Optional[str] = None
    handle: Optional[str] = None
    bio: Optional[str] = None
    website_url: Optional[str] = None
    social_links: Optional[str] = None
    location: Optional[str] = None
    cover_image_url: Optional[str] = None
    pronouns: Optional[str] = None
    tagline: Optional[str] = None

    @classmethod
    def _validate(cls, data: dict) -> "UpdateProfileRequest":
        name = data.get("name")
        avatar_url = data.get("avatar_url")
        handle = data.get("handle")
        bio = data.get("bio")
        website_url = data.get("website_url")
        social_links = data.get("social_links")
        location = data.get("location")
        cover_image_url = data.get("cover_image_url")
        pronouns = data.get("pronouns")
        tagline = data.get("tagline")

        # At least one field must be provided
        if all(
            v is None
            for v in [
                name,
                avatar_url,
                handle,
                bio,
                website_url,
                social_links,
                location,
                cover_image_url,
                pronouns,
                tagline,
            ]
        ):
            raise ValueError("At least one profile field must be provided")

        # Validate name if provided
        if name is not None:
            name = str(name).strip()
            if len(name) == 0:
                raise ValueError("Name cannot be empty")
            if len(name) > 100:
                raise ValueError("Name cannot be longer than 100 characters")

        # Validate handle if provided
        if handle is not None:
            handle = str(handle).strip().lower()
            if not _HANDLE_RE.match(handle):
                raise ValueError("Handle must be 3-40 chars: letters, digits, _ or -")

        # Validate bio length
        if bio is not None:
            bio = str(bio).strip()
            if len(bio) > 500:
                raise ValueError("Bio cannot be longer than 500 characters")

        # Validate tagline length
        if tagline is not None:
            tagline = str(tagline).strip()
            if len(tagline) > 160:
                raise ValueError("Tagline cannot be longer than 160 characters")

        # Validate location length
        if location is not None:
            location = str(location).strip()
            if len(location) > 100:
                raise ValueError("Location cannot be longer than 100 characters")

        # Validate pronouns length
        if pronouns is not None:
            pronouns = str(pronouns).strip()
            if len(pronouns) > 50:
                raise ValueError("Pronouns cannot be longer than 50 characters")

        # social_links stored as JSON string
        if social_links is not None:
            import json as _json

            if isinstance(social_links, dict):
                social_links = _json.dumps(social_links)
            else:
                social_links = str(social_links).strip()

        return cls(
            name=name,
            avatar_url=avatar_url,
            handle=handle,
            bio=bio,
            website_url=website_url,
            social_links=social_links,
            location=location,
            cover_image_url=cover_image_url,
            pronouns=pronouns,
            tagline=tagline,
        )


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
