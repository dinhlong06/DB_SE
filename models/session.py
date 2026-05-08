import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Flashcard(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    front: str
    back: str


class ImageData(BaseModel):
    url: str
    storage_path: str
    filename: str
    size_bytes: int


class ScanData(BaseModel):
    text: str
    scanned_at: datetime


class SummaryData(BaseModel):
    content: str
    generated_at: datetime


class SessionResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    image: ImageData
    scan: Optional[ScanData] = None
    summary: Optional[SummaryData] = None
    flashcards: List[Flashcard] = []
    shared_with: List[str] = []  # Danh sách group_id mà session này được chia sẻ

    class Config:
        populate_by_name = True


# --- Update schemas (dùng cho PATCH/POST endpoints) ---

class UpdateScan(BaseModel):
    text: str
