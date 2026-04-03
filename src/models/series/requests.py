from dataclasses import dataclass
from typing import Optional
from models.base import BaseRequest


def _normalize_optional_text(value) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "undefined" or text.lower() == "null":
        return None
    return text


@dataclass
class SeriesCreateRequest(BaseRequest):
    """Create a new series."""

    name: str
    description: Optional[str] = None
    cover_image_url: Optional[str] = None

    @classmethod
    def _validate(cls, data: dict) -> "SeriesCreateRequest":
        name = data.get("name")
        if not name:
            raise ValueError("Series name is required")
        name = str(name).strip()
        if len(name) < 3:
            raise ValueError("Series name must be at least 3 characters")
        if len(name) > 100:
            raise ValueError("Series name cannot be longer than 100 characters")

        description = _normalize_optional_text(data.get("description"))
        if description and len(description) > 1000:
            raise ValueError("Series description cannot exceed 1000 characters")

        cover_image_url = _normalize_optional_text(data.get("cover_image_url"))

        return cls(
            name=name,
            description=description,
            cover_image_url=cover_image_url,
        )


@dataclass
class SeriesUpdateRequest(BaseRequest):
    """Update a series."""

    name: Optional[str] = None
    description: Optional[str] = None
    cover_image_url: Optional[str] = None

    @classmethod
    def _validate(cls, data: dict) -> "SeriesUpdateRequest":
        name = data.get("name")
        if name is not None:
            name = str(name).strip()
            if len(name) < 3:
                raise ValueError("Series name must be at least 3 characters")
            if len(name) > 100:
                raise ValueError("Series name cannot be longer than 100 characters")

        description = data.get("description")
        if description is not None:
            description = _normalize_optional_text(description)
            if description and len(description) > 1000:
                raise ValueError("Series description cannot exceed 1000 characters")

        cover_image_url = _normalize_optional_text(data.get("cover_image_url"))

        return cls(
            name=name,
            description=description,
            cover_image_url=cover_image_url,
        )


@dataclass
class ArticleSeriesAssignRequest(BaseRequest):
    """Assign an article to a series."""

    series_id: str
    part_number: int

    @classmethod
    def _validate(cls, data: dict) -> "ArticleSeriesAssignRequest":
        series_id = data.get("series_id")
        if not series_id:
            raise ValueError("series_id is required")

        part_number = data.get("part_number")
        if part_number is None:
            raise ValueError("part_number is required")
        try:
            part_number = int(part_number)
            if part_number < 1:
                raise ValueError("part_number must be >= 1")
        except (ValueError, TypeError):
            raise ValueError("Invalid part_number")

        return cls(
            series_id=series_id,
            part_number=part_number,
        )
