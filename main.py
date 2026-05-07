from fastapi import FastAPI
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from routers import auth_router, session_router
import firebase_admin
from firebase_admin import credentials

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

# Khởi tạo Firebase Admin SDK
try:
    cred = credentials.Certificate("firebase-credentials.json")
    firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"Lỗi khởi tạo Firebase: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = AsyncIOMotorClient(MONGO_URI)
    app.mongodb = app.mongodb_client["seapp_db"]
    yield
    app.mongodb_client.close()

app = FastAPI(lifespan=lifespan, title="SEAPP Backend API")

# Đăng ký các Router
app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
app.include_router(session_router.router, prefix="/api/sessions", tags=["sessions"])

@app.get("/")
async def root():
    return {"message": "Welcome to SEAPP Backend! Go to /docs for Swagger UI."}
