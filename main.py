from fastapi import FastAPI
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from routers import scan_router

# Đọc file .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi động cùng hệ thống: Kết nối Database
    app.mongodb_client = AsyncIOMotorClient(MONGO_URI)
    # Tên database tạm sử dụng là seapp_db
    app.mongodb = app.mongodb_client["seapp_db"]
    yield
    # Tắt hệ thống: Đóng kết nối
    app.mongodb_client.close()

app = FastAPI(lifespan=lifespan, title="SEAPP Backend API")

# Đăng ký Router
app.include_router(scan_router.router, prefix="/api/scans", tags=["scans"])

@app.get("/")
async def root():
    return {"message": "Welcome to SEAPP Backend! Go to /docs for Swagger UI."}
