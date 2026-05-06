from pydantic import BaseModel, Field
from datetime import datetime


class ImageResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    filename: str
    content_type: str
    size_bytes: int
    image_url: str      # Public download URL từ Firebase Storage
    storage_path: str   # Đường dẫn file trong bucket (dùng để xoá)
    uploaded_at: datetime

    class Config:
        populate_by_name = True
