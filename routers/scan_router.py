from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

router = APIRouter()

# Schema cho dữ liệu nhận từ Client
class ScanCreate(BaseModel):
    user_id: str
    text: str
    date: Optional[datetime] = Field(default_factory=datetime.utcnow)

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

class ScanResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    text: str
    date: datetime

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

@router.post("/", status_code=201)
async def create_scan(scan: ScanCreate, request: Request):
    """
    Lưu lịch sử từ OCR lên MongoDB (có gắn user_id).
    """
    db = request.app.mongodb
    scan_doc = scan.model_dump()
    result = await db["scan_history"].insert_one(scan_doc)
    
    return {
        "message": "Lưu thành công!",
        "data": {
            "id": str(result.inserted_id),
            "user_id": scan.user_id,
            "text": scan.text,
            "date": scan.date.isoformat()
        }
    }

@router.get("/", response_model=List[ScanResponse])
async def get_scans(request: Request, user_id: str, limit: int = 10):
    """
    Lấy danh sách 10 bản ghi lịch sử mới nhất của một user cụ thể.
    """
    db = request.app.mongodb
    # Tìm bản ghi của riêng user_id này, sắp xếp theo thời gian mới nhất (giảm dần)
    scans_cursor = db["scan_history"].find({"user_id": user_id}).sort("date", -1).limit(limit)
    
    scans = await scans_cursor.to_list(length=limit)
    
    # Ép kiểu _id thành string
    for doc in scans:
        doc["_id"] = str(doc["_id"])
        
    return scans
