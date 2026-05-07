import os
import uuid
from datetime import datetime, timezone
from typing import List

import cloudinary
import cloudinary.uploader
from bson import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel

from models.session import Flashcard, SessionResponse, UpdateScan
from utils.security import get_current_user

router = APIRouter()

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def configure_cloudinary():
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        secure=True,
    )


# ---------------------------------------------------------------------------
# Update schemas (nhận data từ AI bên ngoài)
# ---------------------------------------------------------------------------

class UpdateSummary(BaseModel):
    title: str          # AI sinh tiêu đề
    content: str        # AI sinh tóm tắt

class UpdateFlashcards(BaseModel):
    cards: List[Flashcard]  # AI sinh danh sách thẻ


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_session(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Tạo session mới: upload ảnh lên Cloudinary, khởi tạo document trong MongoDB.
    scan / summary / flashcards ban đầu là null / [].
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Định dạng không hỗ trợ: {file.content_type}.",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Ảnh quá lớn. Giới hạn tối đa là 5 MB.",
        )

    # Upload lên Cloudinary
    configure_cloudinary()
    try:
        public_id = f"seapp/sessions/{current_user['_id']}/{uuid.uuid4().hex}"
        upload_result = cloudinary.uploader.upload(
            contents,
            public_id=public_id,
            resource_type="image",
            overwrite=False,
        )
        image_url = upload_result["secure_url"]
        storage_path = upload_result["public_id"]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi upload ảnh lên Cloudinary: {str(e)}",
        )

    now = datetime.now(timezone.utc)
    session_doc = {
        "user_id": current_user["_id"],
        "title": "",        # AI sẽ điền sau qua PATCH /summary
        "created_at": now,
        "updated_at": now,
        "image": {
            "url": image_url,
            "storage_path": storage_path,
            "filename": file.filename,
            "size_bytes": len(contents),
        },
        "scan": None,
        "summary": None,
        "flashcards": [],
    }

    db = request.app.mongodb
    result = await db["scan_sessions"].insert_one(session_doc)

    return {
        "message": "Tạo session thành công!",
        "session_id": str(result.inserted_id),
        "image_url": image_url,
    }


@router.get("/", response_model=List[SessionResponse])
async def get_sessions(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Lấy danh sách tất cả session của user, mới nhất lên đầu."""
    db = request.app.mongodb
    cursor = db["scan_sessions"].find({"user_id": current_user["_id"]}).sort("created_at", -1)
    sessions = await cursor.to_list(length=100)
    for s in sessions:
        s["_id"] = str(s["_id"])
    return sessions


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Lấy chi tiết đầy đủ của 1 session theo ID."""
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="session_id không hợp lệ.")

    db = request.app.mongodb
    session = await db["scan_sessions"].find_one(
        {"_id": ObjectId(session_id), "user_id": current_user["_id"]}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy session.")

    session["_id"] = str(session["_id"])
    return session


@router.delete("/{session_id}", status_code=200)
async def delete_session(
    session_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Xoá session: xoá ảnh khỏi Cloudinary và document khỏi MongoDB."""
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="session_id không hợp lệ.")

    db = request.app.mongodb
    session = await db["scan_sessions"].find_one(
        {"_id": ObjectId(session_id), "user_id": current_user["_id"]}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy session.")

    configure_cloudinary()
    try:
        cloudinary.uploader.destroy(session["image"]["storage_path"], resource_type="image")
    except Exception:
        pass  # Không block nếu Cloudinary lỗi

    await db["scan_sessions"].delete_one({"_id": ObjectId(session_id)})
    return {"message": "Xoá session thành công!"}


# ---------------------------------------------------------------------------
# Bước 1: Nhận kết quả OCR từ app / AI
# ---------------------------------------------------------------------------

@router.patch("/{session_id}/scan", status_code=200)
async def update_scan(
    session_id: str,
    body: UpdateScan,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Lưu kết quả OCR text vào session."""
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="session_id không hợp lệ.")

    db = request.app.mongodb
    session = await db["scan_sessions"].find_one(
        {"_id": ObjectId(session_id), "user_id": current_user["_id"]}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy session.")

    now = datetime.now(timezone.utc)
    await db["scan_sessions"].update_one(
        {"_id": ObjectId(session_id)},
        {"$set": {
            "scan": {"text": body.text, "scanned_at": now},
            "updated_at": now,
        }},
    )
    return {"message": "Cập nhật OCR thành công!"}


# ---------------------------------------------------------------------------
# Bước 2: Nhận title + summary từ AI
# ---------------------------------------------------------------------------

@router.patch("/{session_id}/summary", status_code=200)
async def update_summary(
    session_id: str,
    body: UpdateSummary,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Lưu title và summary do AI sinh ra vào session.
    Title và summary được gửi cùng lúc để đảm bảo nhất quán.
    """
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="session_id không hợp lệ.")

    db = request.app.mongodb
    session = await db["scan_sessions"].find_one(
        {"_id": ObjectId(session_id), "user_id": current_user["_id"]}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy session.")

    now = datetime.now(timezone.utc)
    await db["scan_sessions"].update_one(
        {"_id": ObjectId(session_id)},
        {"$set": {
            "title": body.title,
            "summary": {"content": body.content, "generated_at": now},
            "updated_at": now,
        }},
    )
    return {"message": "Cập nhật summary thành công!"}


# ---------------------------------------------------------------------------
# Bước 3: Nhận flashcard từ AI
# ---------------------------------------------------------------------------

@router.patch("/{session_id}/flashcards", status_code=200)
async def update_flashcards(
    session_id: str,
    body: UpdateFlashcards,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Lưu danh sách flashcard do AI sinh ra vào session."""
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="session_id không hợp lệ.")

    db = request.app.mongodb
    session = await db["scan_sessions"].find_one(
        {"_id": ObjectId(session_id), "user_id": current_user["_id"]}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy session.")

    cards = [c.model_dump() for c in body.cards]
    now = datetime.now(timezone.utc)
    await db["scan_sessions"].update_one(
        {"_id": ObjectId(session_id)},
        {"$set": {"flashcards": cards, "updated_at": now}},
    )
    return {"message": f"Cập nhật {len(cards)} flashcard thành công!"}
