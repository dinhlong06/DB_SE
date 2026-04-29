from fastapi import APIRouter, Request, HTTPException, Depends
from typing import List
from utils.security import get_current_user
from models.scan import ScanCreate, ScanResponse

router = APIRouter()

@router.post("/", status_code=201)
async def create_scan(
    scan: ScanCreate, 
    request: Request, 
    current_user: dict = Depends(get_current_user)
):
    """
    Lưu lịch sử từ OCR lên MongoDB. user_id được lấy tự động từ Token.
    """
    db = request.app.mongodb
    scan_doc = scan.model_dump()
    
    # Gán user_id từ người dùng đang đăng nhập
    scan_doc["user_id"] = current_user["_id"]
    
    result = await db["scan_history"].insert_one(scan_doc)
    
    return {
        "message": "Lưu thành công!",
        "data": {
            "id": str(result.inserted_id),
            "user_id": scan_doc["user_id"],
            "text": scan.text,
            "date": scan.date.isoformat()
        }
    }

@router.get("/", response_model=List[ScanResponse])
async def get_scans(
    request: Request, 
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """
    Lấy danh sách 10 bản ghi lịch sử mới nhất của người dùng đang đăng nhập.
    """
    db = request.app.mongodb
    user_id = current_user["_id"]
    
    # Tìm bản ghi của riêng user_id này
    scans_cursor = db["scan_history"].find({"user_id": user_id}).sort("date", -1).limit(limit)
    
    scans = await scans_cursor.to_list(length=limit)
    
    # Ép kiểu _id thành string
    for doc in scans:
        doc["_id"] = str(doc["_id"])
        
    return scans
