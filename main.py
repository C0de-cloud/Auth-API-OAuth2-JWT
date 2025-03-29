import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from app.routes.auth import router as auth_router
from app.routes.users import router as users_router

# Загрузка переменных окружения
load_dotenv()

app = FastAPI(
    title="Auth API",
    description="OAuth2 и JWT аутентификация с MongoDB",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшне указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    app.mongodb = app.mongodb_client[os.getenv("MONGODB_DB_NAME")]
    
    # Создание индексов для пользователей
    await app.mongodb.users.create_index("email", unique=True)
    await app.mongodb.users.create_index("username", unique=True)

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()

# Подключение роутеров
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/users", tags=["users"])

@app.get("/")
async def root():
    return {"message": "Welcome to Auth API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 