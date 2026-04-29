from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from models.user import UserCreate, UserLogin, UserInDB, UserResponse, Token
from utils.security import get_password_hash, verify_password, create_access_token
from datetime import datetime
from bson import ObjectId

router = APIRouter()

@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate, request: Request):
    db = request.app.mongodb
    
    # 1. Kiểm tra username đã tồn tại chưa
    existing_user = await db["users"].find_one({"username": user.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
        
    # 2. Kiểm tra email đã tồn tại chưa
    existing_email = await db["users"].find_one({"email": user.email})
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 3. Hash mật khẩu và lưu người dùng mới
    hashed_password = get_password_hash(user.password)
    new_user_dict = UserInDB(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
        created_at=datetime.utcnow()
    ).dict()
    
    result = await db["users"].insert_one(new_user_dict)
    
    # 4. Lấy lại user vừa tạo để trả về thông tin (Response)
    created_user = await db["users"].find_one({"_id": result.inserted_id})
    created_user["_id"] = str(created_user["_id"])
    
    # 5. Tự động cấp Token (Auto-login)
    access_token = create_access_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": created_user
    }

@router.post("/login", response_model=Token)
async def login(request: Request, credentials: OAuth2PasswordRequestForm = Depends()):
    db = request.app.mongodb
    
    # 1. Tìm user theo username
    user = await db["users"].find_one({"username": credentials.username})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 2. Kiểm tra mật khẩu
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Tạo Token
    access_token = create_access_token(data={"sub": user["username"]})
    
    # Chuẩn bị dữ liệu user để trả về
    user["_id"] = str(user["_id"])
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }
