from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum
from datetime import datetime
from bson import ObjectId

class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"

class UserSync(BaseModel):
    """Data received from Frontend to sync Firebase user to MongoDB"""
    uid: str
    email: EmailStr
    username: Optional[str] = None
    role: UserRole = UserRole.STUDENT

class UserResponse(BaseModel):
    """Data returned to Frontend"""
    id: str = Field(alias="_id")
    uid: str
    email: EmailStr
    username: Optional[str] = None
    role: UserRole
    created_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class UserInDB(BaseModel):
    """Data stored in MongoDB"""
    uid: str
    email: EmailStr
    username: Optional[str] = None
    role: UserRole
    created_at: datetime = Field(default_factory=datetime.utcnow)
