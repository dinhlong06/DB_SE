from fastapi import APIRouter, Request, HTTPException, status
from models.user import UserSync, UserInDB, UserResponse
from datetime import datetime

router = APIRouter()

@router.post("/sync-user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def sync_user(user: UserSync, request: Request):
    """
    API này được Frontend gọi NGAY SAU KHI đăng nhập/đăng ký bằng Firebase thành công.
    Nó sẽ kiểm tra xem UID này đã có trong MongoDB chưa, nếu chưa thì tạo mới với role tương ứng.
    """
    db = request.app.mongodb
    
    # 1. Kiểm tra xem user (uid) đã tồn tại trong Mongo chưa
    existing_user = await db["users"].find_one({"uid": user.uid})
    if existing_user:
        # Nếu đã có rồi thì trả về luôn, không cần báo lỗi
        existing_user["_id"] = str(existing_user["_id"])
        return existing_user
        
    # 2. Tạo bản ghi mới trong MongoDB
    new_user_dict = UserInDB(
        uid=user.uid,
        email=user.email,
        username=user.username,
        role=user.role,
        created_at=datetime.utcnow()
    ).dict()
    
    result = await db["users"].insert_one(new_user_dict)
    
    # 3. Lấy lại user vừa tạo để trả về (Response)
    created_user = await db["users"].find_one({"_id": result.inserted_id})
    created_user["_id"] = str(created_user["_id"])
    
    return created_user
