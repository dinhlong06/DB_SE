from datetime import datetime, timezone
from typing import List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status

from models.group import AddMember, GroupCreate, GroupResponse
from utils.security import get_current_user

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def require_teacher(current_user: dict):
    """Raise 403 nếu user không phải Teacher."""
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Teacher mới có quyền thực hiện thao tác này.",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_group(
    body: GroupCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Tạo nhóm mới. Chỉ Teacher mới được tạo."""
    require_teacher(current_user)

    db = request.app.mongodb
    now = datetime.now(timezone.utc)
    group_doc = {
        "name": body.name,
        "description": body.description,
        "teacher_id": current_user["_id"],
        "members": [],
        "created_at": now,
    }

    result = await db["groups"].insert_one(group_doc)
    return {
        "message": "Tạo nhóm thành công!",
        "group_id": str(result.inserted_id),
    }


@router.get("/", response_model=List[GroupResponse])
async def get_my_groups(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Lấy danh sách nhóm mà user liên quan:
    - Teacher: nhóm mình tạo
    - Student: nhóm mình là member
    """
    db = request.app.mongodb
    uid = current_user["_id"]

    if current_user.get("role") == "teacher":
        query = {"teacher_id": uid}
    else:
        query = {"members": uid}

    cursor = db["groups"].find(query).sort("created_at", -1)
    groups = await cursor.to_list(length=100)
    for g in groups:
        g["_id"] = str(g["_id"])
    return groups


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Lấy chi tiết nhóm. Chỉ teacher hoặc member mới được xem."""
    if not ObjectId.is_valid(group_id):
        raise HTTPException(status_code=400, detail="group_id không hợp lệ.")

    db = request.app.mongodb
    group = await db["groups"].find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhóm.")

    uid = current_user["_id"]
    if group["teacher_id"] != uid and uid not in group.get("members", []):
        raise HTTPException(status_code=403, detail="Bạn không có quyền xem nhóm này.")

    group["_id"] = str(group["_id"])
    return group


@router.delete("/{group_id}", status_code=200)
async def delete_group(
    group_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Xoá nhóm. Chỉ Teacher tạo nhóm mới được xoá."""
    require_teacher(current_user)

    if not ObjectId.is_valid(group_id):
        raise HTTPException(status_code=400, detail="group_id không hợp lệ.")

    db = request.app.mongodb
    group = await db["groups"].find_one(
        {"_id": ObjectId(group_id), "teacher_id": current_user["_id"]}
    )
    if not group:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhóm hoặc bạn không có quyền xoá.")

    await db["groups"].delete_one({"_id": ObjectId(group_id)})
    return {"message": "Xoá nhóm thành công!"}


@router.post("/{group_id}/members", status_code=200)
async def add_member(
    group_id: str,
    body: AddMember,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Thêm member vào nhóm. Chỉ Teacher tạo nhóm mới được thêm."""
    require_teacher(current_user)

    if not ObjectId.is_valid(group_id):
        raise HTTPException(status_code=400, detail="group_id không hợp lệ.")

    db = request.app.mongodb
    group = await db["groups"].find_one(
        {"_id": ObjectId(group_id), "teacher_id": current_user["_id"]}
    )
    if not group:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhóm hoặc bạn không có quyền.")

    # Kiểm tra user cần thêm có tồn tại không
    user = await db["users"].find_one({"_id": ObjectId(body.user_id)}) \
        if ObjectId.is_valid(body.user_id) else None
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy user.")

    # $addToSet tránh thêm trùng
    await db["groups"].update_one(
        {"_id": ObjectId(group_id)},
        {"$addToSet": {"members": body.user_id}},
    )
    return {"message": f"Đã thêm user vào nhóm thành công!"}


@router.delete("/{group_id}/members/{user_id}", status_code=200)
async def remove_member(
    group_id: str,
    user_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Xoá member khỏi nhóm. Chỉ Teacher tạo nhóm mới được xoá."""
    require_teacher(current_user)

    if not ObjectId.is_valid(group_id):
        raise HTTPException(status_code=400, detail="group_id không hợp lệ.")

    db = request.app.mongodb
    group = await db["groups"].find_one(
        {"_id": ObjectId(group_id), "teacher_id": current_user["_id"]}
    )
    if not group:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhóm hoặc bạn không có quyền.")

    await db["groups"].update_one(
        {"_id": ObjectId(group_id)},
        {"$pull": {"members": user_id}},
    )
    return {"message": "Xoá member thành công!"}


@router.get("/{group_id}/sessions")
async def get_group_sessions(
    group_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Lấy danh sách sessions được Teacher chia sẻ vào nhóm."""
    if not ObjectId.is_valid(group_id):
        raise HTTPException(status_code=400, detail="group_id không hợp lệ.")

    db = request.app.mongodb
    group = await db["groups"].find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhóm.")

    uid = current_user["_id"]
    if group["teacher_id"] != uid and uid not in group.get("members", []):
        raise HTTPException(status_code=403, detail="Bạn không có quyền xem nhóm này.")

    cursor = db["scan_sessions"].find(
        {"shared_with": group_id}
    ).sort("created_at", -1)
    sessions = await cursor.to_list(length=100)
    for s in sessions:
        s["_id"] = str(s["_id"])
    return sessions
