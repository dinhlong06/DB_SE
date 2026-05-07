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
- **User Sync**: Đồng bộ tài khoản Firebase → MongoDB sau khi đăng nhập/đăng ký.
- **Role-based Access**: Phân quyền Student / Teacher.
- **Scan Sessions**: Mỗi session gom toàn bộ dữ liệu 1 lần scan (ảnh + OCR + summary + flashcard) vào 1 document MongoDB.
- **Image Upload**: Upload ảnh lên Cloudinary, lưu URL vào session.
- **Partial Update**: AI bên ngoài cập nhật từng phần (scan / summary / flashcard) theo từng bước xử lý.

## 📂 Project Structure

```text
backend/
├── main.py                      # FastAPI app instance & lifespan (MongoDB connect)
├── models/
│   ├── user.py                  # UserSync, UserInDB, UserResponse
│   └── session.py               # SessionResponse, Flashcard, UpdateScan, ...
├── routers/
│   ├── auth_router.py           # POST /api/auth/sync-user
│   └── session_router.py        # CRUD + partial update /api/sessions/
├── utils/
│   └── security.py              # Firebase token verification, get_current_user
├── firebase-credentials.json    # Firebase Admin SDK key (KHÔNG commit)
├── requirements.txt
└── .env                         # Biến môi trường (KHÔNG commit)
```

## 📡 API Endpoints

### Auth
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `POST` | `/api/auth/sync-user` | Đồng bộ user Firebase → MongoDB |

### Sessions
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `POST` | `/api/sessions/` | Tạo session mới + upload ảnh lên Cloudinary |
| `GET` | `/api/sessions/` | Lấy danh sách session của user |
| `GET` | `/api/sessions/{id}` | Lấy chi tiết 1 session (ảnh + scan + summary + flashcard) |
| `DELETE` | `/api/sessions/{id}` | Xoá session + xoá ảnh khỏi Cloudinary |
| `PATCH` | `/api/sessions/{id}/scan` | Lưu kết quả OCR text |
| `PATCH` | `/api/sessions/{id}/summary` | Lưu title + summary do AI sinh |
| `PATCH` | `/api/sessions/{id}/flashcards` | Lưu danh sách flashcard do AI sinh |

> Tất cả endpoint (trừ `/api/auth/sync-user`) đều yêu cầu **Bearer Token** (Firebase ID Token).

### MongoDB Document (collection: `scan_sessions`)

```json
{
  "_id": "ObjectId",
  "user_id": "string",
  "title": "string (AI sinh khi PATCH summary)",
  "created_at": "datetime",
  "updated_at": "datetime",
  "image": { "url": "...", "storage_path": "...", "filename": "...", "size_bytes": 0 },
  "scan": { "text": "OCR text...", "scanned_at": "datetime" },
  "summary": { "content": "Tóm tắt...", "generated_at": "datetime" },
  "flashcards": [{ "id": "uuid", "front": "Câu hỏi?", "back": "Câu trả lời" }]
}
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

## ☁️ Deployment (Render)

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`

Thêm các biến trong `.env` vào Render dashboard. Whitelist `0.0.0.0/0` trong MongoDB Network Access.