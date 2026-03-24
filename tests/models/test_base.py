from dataclasses import dataclass

import pytest

from models.base import BaseModel, BaseRequest, row_get


@dataclass
class ChildModel(BaseModel):
    value: str


@dataclass
class ParentModel(BaseModel):
    name: str
    child: ChildModel | None = None
    items: list | None = None
    optional: str | None = None


@dataclass
class DemoRequest(BaseRequest):
    name: str
    count: int = 0

    @classmethod
    def _validate(cls, data: dict) -> "DemoRequest":
        if not data.get("name"):
            raise ValueError("name is required")
        return cls(name=data["name"], count=int(data.get("count", 0)))


class ObjRow:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestRowGet:
    def test_row_get_handles_dict_and_object(self):
        assert row_get({"k": "v"}, "k") == "v"
        assert row_get({"k": "v"}, "missing", "d") == "d"
        assert row_get(ObjRow(k="v"), "k") == "v"
        assert row_get(ObjRow(), "missing", "d") == "d"


class TestBaseModel:
    def test_to_dict_and_to_json_with_nested_models_and_lists(self):
        model = ParentModel(
            name="parent",
            child=ChildModel(value="child"),
            items=[ChildModel(value="nested"), "plain"],
            optional=None,
        )

        payload = model.to_dict()
        assert payload == {
            "name": "parent",
            "child": {"value": "child"},
            "items": [{"value": "nested"}, "plain"],
        }
        assert (
            model.to_json()
            == '{"name": "parent", "child": {"value": "child"}, "items": [{"value": "nested"}, "plain"]}'
        )

    def test_base_model_from_row_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            BaseModel.from_row({})


class TestBaseRequest:
    def test_from_body_accepts_dict(self):
        req = DemoRequest.from_body({"name": "alpha", "count": 2})
        assert req.name == "alpha"
        assert req.count == 2

    def test_from_body_accepts_object_proxy(self):
        req = DemoRequest.from_body(ObjRow(name="beta", count=3, ignored="x"))
        assert req.name == "beta"
        assert req.count == 3

    def test_from_body_raises_validation_error(self):
        with pytest.raises(ValueError):
            DemoRequest.from_body({"name": ""})

    def test_validate_not_implemented_raises(self):
        with pytest.raises(NotImplementedError):
            BaseRequest._validate({})
