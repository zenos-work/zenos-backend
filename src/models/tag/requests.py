from dataclasses import dataclass
from models.base import BaseRequest


@dataclass
class TagCreateRequest(BaseRequest):
    name: str
    tag_type: str = "topic"

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

        return cls(name=name, tag_type=tag_type)
