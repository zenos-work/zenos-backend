from dataclasses import dataclass
from models.base import BaseRequest


@dataclass
class TagCreateRequest(BaseRequest):
    name: str
    tag_type: str = "topic"
    category_slug: str | None = None
    is_onboarding_category: int = 0

    @classmethod
    def _validate(cls, data: dict) -> "TagCreateRequest":
        if "name" not in data or not isinstance(data["name"], str):
            raise ValueError("Field 'name' is required and must be a string.")

        name = data["name"].strip().lstrip("#").strip()
        if len(name) == 0 or len(name) > 50:
            raise ValueError("Field 'name' cannot be empty or exceed 50 characters.")

        raw_type = data.get("tag_type", "topic")
        tag_type = str(raw_type).strip().lower()
        if tag_type not in {"topic", "outcome"}:
            raise ValueError("Field 'tag_type' must be 'topic' or 'outcome'.")

        raw_category = data.get("category_slug")
        category_slug = None
        if raw_category is not None:
            if not isinstance(raw_category, str):
                raise ValueError(
                    "Field 'category_slug' must be a string when provided."
                )
            category_slug = raw_category.strip().lower().replace(" ", "-")
            if len(category_slug) == 0:
                category_slug = None

        raw_flag = data.get("is_onboarding_category", False)
        is_onboarding_category = 1 if bool(raw_flag) else 0

        return cls(
            name=name,
            tag_type=tag_type,
            category_slug=category_slug,
            is_onboarding_category=is_onboarding_category,
        )
