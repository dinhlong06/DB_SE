from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth

security = HTTPBearer()

async def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Giải mã và xác thực Token bằng Firebase Admin
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token.get("uid")
        
        # Bắt buộc xác minh email (vì lúc trước bạn có yêu cầu tính năng này)
        # Bỏ comment 4 dòng dưới đây nếu bạn muốn bắt buộc user phải xác minh email mới được gọi API
        # if not decoded_token.get("email_verified", False):
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Email is not verified. Please check your inbox."
        #     )
            
        if not uid:
            raise credentials_exception
    except Exception as e:
        print(f"Token verification error: {e}")
        raise credentials_exception
    
    db = request.app.mongodb
    # Tìm user trong MongoDB bằng uid
    user = await db["users"].find_one({"uid": uid})
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in database. Please sync user first."
        )
    
    user["_id"] = str(user["_id"])
    return user
