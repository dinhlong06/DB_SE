import uuid
from datetime import datetime, timezone
from typing import List

import cloudinary
import cloudinary.uploader
from bson import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import RedirectResponse

from models.image import ImageResponse
from utils.security import get_current_user

import os


router = APIRouter()

# Giới hạn kích thước ảnh: 5 MB
MAX_FILE_SIZE = 5 * 1024 * 1024

# Các định dạng ảnh được chấp nhận
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def configure_cloudinary():
    """Cấu hình Cloudinary từ biến môi trường (đọc lại mỗi lần gọi để đảm bảo .env đã load)."""
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        secure=True,  # Luôn dùng HTTPS
    )


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload ảnh lên Cloudinary. URL download sẽ được lưu vào MongoDB.
    Yêu cầu xác thực JWT.
    """
    # Kiểm tra định dạng file
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Định dạng không hỗ trợ: {file.content_type}. Chỉ chấp nhận: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )

    # Đọc nội dung file
    contents = await file.read()

    # Kiểm tra kích thước
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Ảnh quá lớn. Giới hạn tối đa là 5 MB.",
        )

    # Upload lên Cloudinary
    configure_cloudinary()
    try:
        # public_id duy nhất: images/<user_id>/<uuid>
        public_id = f"seapp/images/{current_user['_id']}/{uuid.uuid4().hex}"
        upload_result = cloudinary.uploader.upload(
            contents,
            public_id=public_id,
            resource_type="image",
            overwrite=False,
        )
        image_url = upload_result["secure_url"]       # https://res.cloudinary.com/...
        storage_path = upload_result["public_id"]     # dùng để xoá sau này
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi upload lên Cloudinary: {str(e)}",
        )

    # Lưu metadata vào MongoDB
    db = request.app.mongodb
    image_doc = {
        "user_id": current_user["_id"],
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(contents),
        "image_url": image_url,
        "storage_path": storage_path,
        "uploaded_at": datetime.now(timezone.utc),
    }

    result = await db["images"].insert_one(image_doc)

    return {
        "message": "Upload ảnh thành công!",
        "data": {
            "id": str(result.inserted_id),
            "filename": file.filename,
            "size_bytes": len(contents),
            "content_type": file.content_type,
            "image_url": image_url,
        },
    }


@router.get("/", response_model=List[ImageResponse])
async def get_my_images(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Lấy danh sách tất cả ảnh của người dùng hiện tại (metadata + URL Cloudinary).
    """
    db = request.app.mongodb
    cursor = db["images"].find({"user_id": current_user["_id"]}).sort("uploaded_at", -1)
    images = await cursor.to_list(length=100)

    for img in images:
        img["_id"] = str(img["_id"])

    return images


@router.get("/{image_id}")
async def get_image_by_id(
    image_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Lấy thông tin một ảnh theo ID, redirect đến URL ảnh trên Cloudinary.
    """
    if not ObjectId.is_valid(image_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="image_id không hợp lệ.")

    db = request.app.mongodb
    image_doc = await db["images"].find_one(
        {"_id": ObjectId(image_id), "user_id": current_user["_id"]}
    )

    if not image_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy ảnh.")

    # Redirect thẳng đến URL ảnh trên Cloudinary
    return RedirectResponse(url=image_doc["image_url"])


@router.delete("/{image_id}", status_code=status.HTTP_200_OK)
async def delete_image(
    image_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Xoá ảnh khỏi Cloudinary VÀ MongoDB. Chỉ chủ sở hữu mới được xoá.
    """
    if not ObjectId.is_valid(image_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="image_id không hợp lệ.")

    db = request.app.mongodb
    image_doc = await db["images"].find_one(
        {"_id": ObjectId(image_id), "user_id": current_user["_id"]}
    )

    if not image_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy ảnh hoặc bạn không có quyền xoá.",
        )

    # Xoá file khỏi Cloudinary
    configure_cloudinary()
    try:
        cloudinary.uploader.destroy(image_doc["storage_path"], resource_type="image")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xoá ảnh trên Cloudinary: {str(e)}",
        )

    # Xoá metadata khỏi MongoDB
    await db["images"].delete_one({"_id": ObjectId(image_id)})

    return {"message": "Xoá ảnh thành công!"}
