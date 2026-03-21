import importlib


media_handler = importlib.import_module("api.media.handler")


class _MetadataWithGet:
    def get(self, key):
        if key == "contentType":
            return "image/webp"
        return None


class _MetadataAttr:
    contentType = "image/png"


class _MetadataToPy:
    def to_py(self, depth=3):
        return {"contentType": "image/jpeg"}


class _Obj:
    def __init__(self, metadata):
        self.httpMetadata = metadata


def test_extract_content_type_from_mapping_getter():
    obj = _Obj(_MetadataWithGet())
    assert media_handler._extract_content_type(obj) == "image/webp"


def test_extract_content_type_from_attribute():
    obj = _Obj(_MetadataAttr())
    assert media_handler._extract_content_type(obj) == "image/png"


def test_extract_content_type_from_to_py_mapping():
    obj = _Obj(_MetadataToPy())
    assert media_handler._extract_content_type(obj) == "image/jpeg"


def test_extract_content_type_handles_missing_metadata():
    class _NoMeta:
        pass

    assert media_handler._extract_content_type(_NoMeta()) is None
