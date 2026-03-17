from dataclasses import dataclass, fields
from typing import Any
import json


def row_get(row, key: str, default=None):
    """Safely read from D1 row — dict or JS proxy."""
    return (
        row.get(key, default) if isinstance(row, dict) else getattr(row, key, default)
    )


@dataclass
class BaseModel:
    def to_dict(self, scope: str = "default") -> dict:
        result = {}
        for field in fields(self):
            value = getattr(self, field.name)
            if value is None:
                continue
            if isinstance(value, BaseModel):
                result[field.name] = value.to_dict(scope)
            elif isinstance(value, list):
                result[field.name] = [
                    item.to_dict(scope) if isinstance(item, BaseModel) else item
                    for item in value
                ]
            else:
                result[field.name] = value
        return result

    def to_json(self, scope: str = "default") -> str:
        return json.dumps(self.to_dict(scope))

    @classmethod
    def from_row(cls, row) -> "BaseModel":
        raise NotImplementedError("from_row method must be implemented by subclasses")


@dataclass
class BaseRequest:
    @classmethod
    def from_body(cls, body: Any) -> "BaseRequest":
        """
        Handles both plain dict and Cloudflare JS proxy objects.
        Raises ValueError on validation failure.
        """
        if isinstance(body, dict):
            data = body
        else:
            data = {
                f.name: getattr(body, f.name, None)
                for f in fields(cls)
                if getattr(body, f.name, None) is not None
            }
        return cls._validate(data)

    @classmethod
    def _validate(cls, data: dict) -> "BaseRequest":
        raise NotImplementedError("Validation logic must be implemented by subclasses")
