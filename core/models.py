# FastAPI's jsonable_encoder handles converting various non-JSON types,
# such as datetime between JSON types and native Python types.
from fastapi.encoders import jsonable_encoder

# Pydantic, and Python's built-in typing are used to define a schema
# that defines the structure and types of the different objects stored
# in the recipes collection, and managed by this API.
from pydantic import BaseModel, Field
from typing import List, Optional, Union
from datetime import datetime
from .food import Food, Entry

from .objectid import PydanticObjectId

class User(BaseModel):
    id: Optional[PydanticObjectId] = Field(None, alias="_id")
    name: str
    email: str
    fridge_ids: Optional[List[PydanticObjectId]]
    entries: Optional[List[Entry]]

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)

    def to_bson(self):
        data = self.dict(by_alias=True, exclude_none=True)
        if data.get("_id") is None:
            data.pop("_id", None)
        return data

# Fridge/Food Basket
class Fridge(BaseModel):
    id: Optional[PydanticObjectId] = Field(None, alias="_id")
    slug: str
    users: Optional[List[str]]
    foods: Optional[List[Food]]

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)

    def to_bson(self):
        data = self.dict(by_alias=True, exclude_none=True)
        if data.get("_id") is None:
            data.pop("_id", None)
        return data