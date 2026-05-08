from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class GroupCreate(BaseModel):
    name: str
    description: str = ""


class AddMember(BaseModel):
    user_id: str  # _id của user trong MongoDB


class ShareSession(BaseModel):
    group_ids: List[str]  # Danh sách group_id muốn chia sẻ session


class GroupResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    description: str
    teacher_id: str
    members: List[str] = []
    created_at: datetime

    class Config:
        populate_by_name = True
