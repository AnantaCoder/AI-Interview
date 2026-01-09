from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Any, Optional
from uuid import UUID
import json


def to_snake_case(name: str) -> str:
    import re
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


class AppBaseModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_snake_case,
        str_strip_whitespace=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    )
    
    def to_dict(self, exclude_none: bool = True) -> dict[str, Any]:
        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        return data
    
    def to_json(self) -> str:
        return self.model_dump_json(by_alias=True)
    
    @classmethod
    def from_db_row(cls, row: dict) -> "AppBaseModel":
        return cls.model_validate(row)


class TimestampMixin(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class IdMixin(BaseModel):
    id: Optional[UUID] = None
