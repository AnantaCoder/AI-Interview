import json
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from typing import Any


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, bytes):
            return obj.decode("utf-8")
        return super().default(obj)


def serialize_to_json(data: Any) -> str:
    return json.dumps(data, cls=CustomJSONEncoder, ensure_ascii=False)


def deserialize_from_json(json_str: str) -> Any:
    return json.loads(json_str)


def to_snake_case(name: str) -> str:
    import re
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def to_camel_case(name: str) -> str:
    components = name.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def clean_dict(data: dict, exclude_none: bool = True) -> dict:
    if exclude_none:
        return {k: v for k, v in data.items() if v is not None}
    return data
