# FastAPI's jsonable_encoder handles converting various non-JSON types,
# such as datetime between JSON types and native Python types.
from fastapi.encoders import jsonable_encoder

# Pydantic, and Python's built-in typing are used to define a schema
# that defines the structure and types of the different objects stored
# in the recipes collection, and managed by this API.
from pydantic import BaseModel, Field
from typing import List, Optional, Union
from datetime import datetime

from core.objectid import PydanticObjectId
from uuid import UUID, uuid4


class Food(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    slug: str
    expiration_date: Optional[str]
    cost_per_unit: Optional[float]
    category: str
    quantity: int
    location: Optional[str]

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)

    def to_bson(self):
        data = self.dict(by_alias=True, exclude_none=True)
        if data.get("_id") is None:
            data.pop("_id", None)
        return data

class Entry(BaseModel):
    food_name: str
    category: str
    entry_type: Optional[str]
    amount: int
    cost_per_unit: float
    creation_time: Optional[str]

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)

    def to_bson(self):
        data = self.dict(by_alias=True, exclude_none=True)
        if data.get("_id") is None:
            data.pop("_id", None)
        return data