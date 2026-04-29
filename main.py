from fastapi import FastAPI
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from routers import scan_router, auth_router # Thêm auth_router

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = AsyncIOMotorClient(MONGO_URI)
    app.mongodb = app.mongodb_client["seapp_db"]
    yield
    app.mongodb_client.close()

app = FastAPI(lifespan=lifespan, title="SEAPP Backend API")

# Đăng ký các Router
app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
app.include_router(scan_router.router, prefix="/api/scans", tags=["scans"])

@app.get("/")
async def root():
    return {"message": "Welcome to SEAPP Backend! Go to /docs for Swagger UI."}
