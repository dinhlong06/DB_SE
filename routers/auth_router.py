from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends
from firebase_admin import auth

from models.user import UserSync, UserInDB, UserResponse
from utils.security import get_current_user

router = APIRouter()
security = HTTPBearer()


@router.post("/sync-user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def sync_user(
    user: UserSync,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Frontend gọi NGAY SAU KHI đăng nhập/đăng ký Firebase thành công.
    - uid và email được lấy tự động từ Firebase ID Token.
    - Frontend chỉ cần gửi: username (tùy chọn) và role.
    - Nếu user đã tồn tại → trả về thông tin hiện tại (không ghi đè).
    """
    # Giải mã token để lấy uid và email
    try:
        decoded_token = auth.verify_id_token(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ.",
        )

    uid = decoded_token["uid"]
    email = decoded_token.get("email", "")

    # Fallback username: user nhập → display name Firebase → phần trước @ của email
    username = user.username or decoded_token.get("name") or email.split("@")[0]

    db = request.app.mongodb

    # 1. Nếu user đã tồn tại → trả về luôn
    existing_user = await db["users"].find_one({"uid": uid})
    if existing_user:
        existing_user["_id"] = str(existing_user["_id"])
        return existing_user

    # 2. Tạo bản ghi mới trong MongoDB
    new_user_dict = UserInDB(
        uid=uid,
        email=email,
        username=username,
        role=user.role,
        created_at=datetime.now(timezone.utc),
    ).dict()

    result = await db["users"].insert_one(new_user_dict)

    # 3. Trả về user vừa tạo
    created_user = await db["users"].find_one({"_id": result.inserted_id})
    created_user["_id"] = str(created_user["_id"])

    return created_user


@router.get("/users/search")
async def search_user(
    email: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Tìm user theo email để lấy user_id.
    Teacher dùng endpoint này để lấy _id của student trước khi thêm vào nhóm.
    Trả về thông tin cơ bản (không trả password hay token).
    """
    db = request.app.mongodb
    user = await db["users"].find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy user với email này.",
        )
    return {
        "user_id": str(user["_id"]),
        "username": user.get("username"),
        "email": user.get("email"),
        "role": user.get("role"),
    }
