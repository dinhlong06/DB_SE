from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class ScanCreate(BaseModel):
    text: str
    date: Optional[datetime] = Field(default_factory=datetime.utcnow)

class ScanResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    text: str
    date: datetime

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
