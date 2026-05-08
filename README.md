# SEAPP Backend API

Backend service cho ứng dụng **SEAPP** — ứng dụng quét OCR ảnh, tóm tắt nội dung và tạo flashcard học tập. Được xây dựng bằng **FastAPI** và **MongoDB**.

## 🚀 Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database**: MongoDB Atlas (async via `motor`)
- **Authentication**: Firebase Auth (ID Token verification)
- **Image Storage**: [Cloudinary](https://cloudinary.com/)
- **Server**: Uvicorn

## ✨ Features

- **Firebase Authentication**: Xác thực người dùng bằng Firebase ID Token.
- **User Sync**: Đồng bộ tài khoản Firebase → MongoDB (chỉ cần gửi `username` + `role`, `uid`/`email` tự lấy từ token).
- **Role-based Access**: Phân quyền Student / Teacher.
- **Scan Sessions**: Mỗi session gom toàn bộ dữ liệu 1 lần scan (ảnh + OCR + summary + flashcard) vào 1 document MongoDB.
- **Image Upload**: Upload ảnh lên Cloudinary, lưu URL vào session.
- **Partial Update**: AI bên ngoài cập nhật từng phần (scan / summary / flashcard) theo từng bước xử lý.
- **Groups**: Teacher tạo nhóm, thêm/xoá student, chia sẻ session tài liệu cho cả nhóm.

## 📂 Project Structure

```text
backend/
├── main.py                      # FastAPI app instance & lifespan (MongoDB connect)
├── models/
│   ├── user.py                  # UserSync, UserInDB, UserResponse
│   ├── session.py               # SessionResponse, Flashcard, UpdateScan, ...
│   └── group.py                 # GroupCreate, GroupResponse, AddMember, ShareSession
├── routers/
│   ├── auth_router.py           # Auth & User endpoints
│   ├── session_router.py        # Scan session endpoints
│   └── group_router.py          # Group endpoints
├── utils/
│   └── security.py              # Firebase token verification, get_current_user
├── firebase-credentials.json    # Firebase Admin SDK key (KHÔNG commit)
├── requirements.txt
└── .env                         # Biến môi trường (KHÔNG commit)
```

## 📡 API Endpoints

### Auth & Users — `/api/auth`

| Method | Endpoint | Role | Mô tả |
|--------|----------|------|-------|
| `POST` | `/sync-user` | All | Đồng bộ user Firebase → MongoDB sau khi đăng nhập/đăng ký |
| `GET` | `/users/search?email=` | All | Tìm user theo email (lấy `user_id` để thêm vào nhóm) |

> `POST /sync-user` chỉ cần gửi `{ "username": "...", "role": "student" }`. `uid` và `email` lấy tự động từ token.

### Sessions — `/api/sessions`

| Method | Endpoint | Role | Mô tả |
|--------|----------|------|-------|
| `POST` | `/` | All | Tạo session mới + upload ảnh lên Cloudinary |
| `GET` | `/` | All | Lấy danh sách session của user |
| `GET` | `/{id}` | All | Lấy chi tiết 1 session |
| `DELETE` | `/{id}` | All | Xoá session + xoá ảnh khỏi Cloudinary |
| `PATCH` | `/{id}/scan` | All | Lưu kết quả OCR text |
| `PATCH` | `/{id}/summary` | All | Lưu title + summary do AI sinh |
| `PATCH` | `/{id}/flashcards` | All | Lưu danh sách flashcard do AI sinh |
| `POST` | `/{id}/share` | Teacher | Chia sẻ session với một hoặc nhiều nhóm |

### Groups — `/api/groups`

| Method | Endpoint | Role | Mô tả |
|--------|----------|------|-------|
| `POST` | `/` | Teacher | Tạo nhóm mới |
| `GET` | `/` | All | Lấy danh sách nhóm của user |
| `GET` | `/{id}` | Member/Teacher | Lấy chi tiết nhóm |
| `DELETE` | `/{id}` | Teacher | Xoá nhóm |
| `POST` | `/{id}/members` | Teacher | Thêm student vào nhóm |
| `DELETE` | `/{id}/members/{uid}` | Teacher | Xoá student khỏi nhóm |
| `GET` | `/{id}/sessions` | Member/Teacher | Xem tài liệu được chia sẻ trong nhóm |

> Tất cả endpoint đều yêu cầu **Bearer Token** (Firebase ID Token).

### MongoDB Document (collection: `scan_sessions`)

```json
{
  "_id": "ObjectId",
  "user_id": "string",
  "title": "string (AI sinh khi PATCH /summary)",
  "created_at": "datetime",
  "updated_at": "datetime",
  "image": { "url": "...", "storage_path": "...", "filename": "...", "size_bytes": 0 },
  "scan": { "text": "OCR text...", "scanned_at": "datetime" },
  "summary": { "content": "Tóm tắt...", "generated_at": "datetime" },
  "flashcards": [{ "id": "uuid", "front": "Câu hỏi?", "back": "Câu trả lời" }],
  "shared_with": ["group_id_1", "group_id_2"]
}
```

### MongoDB Document (collection: `groups`)

```json
{
  "_id": "ObjectId",
  "name": "Nhóm Toán 12A",
  "description": "...",
  "teacher_id": "string",
  "members": ["user_id_1", "user_id_2"],
  "created_at": "datetime"
}
```

## 🔄 Luồng sử dụng

### Luồng scan tài liệu

```
1. POST /api/sessions/            → upload ảnh, nhận session_id
2. PATCH /api/sessions/{id}/scan  → gửi OCR text
3. PATCH /api/sessions/{id}/summary    → AI gửi title + summary
4. PATCH /api/sessions/{id}/flashcards → AI gửi danh sách thẻ
5. GET  /api/sessions/{id}        → lấy toàn bộ data
```

### Luồng chia sẻ tài liệu (Teacher)

```
1. POST /api/groups/                          → tạo nhóm, nhận group_id
2. GET  /api/auth/users/search?email=...      → tìm student, nhận user_id
3. POST /api/groups/{id}/members              → thêm student vào nhóm
4. POST /api/sessions/{id}/share              → chia sẻ session với nhóm
5. GET  /api/groups/{id}/sessions             → student xem tài liệu nhóm
```

## 🛠️ Getting Started

### 1. Yêu cầu
- Python 3.8+
- MongoDB Atlas cluster
- Firebase project (có Service Account)
- Cloudinary account

### 2. Clone repository
```bash
git clone https://github.com/dinhlong06/DB_SE.git
cd backend
```

### 3. Tạo Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 4. Cài Dependencies
```bash
pip install -r requirements.txt
```

### 5. Cấu hình Environment Variables
Tạo file `.env` trong thư mục `backend/`:

```env
# MongoDB
MONGO_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/

# Cloudinary (lấy từ https://console.cloudinary.com)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

Đặt file `firebase-credentials.json` (Service Account) vào thư mục `backend/`.

> ⚠️ **Không commit** `.env` và `firebase-credentials.json` lên Git.

### 6. Chạy Server
```bash
python -m uvicorn main:app --reload
```
Server chạy tại: `http://127.0.0.1:8000`

## 📚 API Documentation

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## 🔑 Cách lấy Token để test

```powershell
$response = Invoke-RestMethod `
  -Uri "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=YOUR_WEB_API_KEY" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"email":"your@email.com","password":"yourpassword","returnSecureToken":true}'

$response.idToken
```

Dùng `idToken` làm `Bearer Token` trong Swagger UI hoặc Postman.

> ⚠️ Firebase ID Token **hết hạn sau 1 giờ**. Khi test cần lấy token mới nếu gặp lỗi 401.

## ☁️ Deployment (Render)

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`

Thêm các biến trong `.env` vào Render dashboard. Whitelist `0.0.0.0/0` trong MongoDB Network Access.