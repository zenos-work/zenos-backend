from dataclasses import dataclass
from models.base import BaseRequest


@dataclass
class TagCreateRequest(BaseRequest):
    name: str

    @classmethod
    def _validate(cls, data: dict) -> "TagCreateRequest":
        if "name" not in data or not isinstance(data["name"], str):
            raise ValueError("Field 'name' is required and must be a string.")

        name = data["name"].strip()
        if len(name) == 0 or len(name) > 50:
            raise ValueError("Field 'name' cannot be empty or exceed 50 characters.")

        return cls(name=data["name"])
