from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status

from app.core.security import get_password_hash, verify_password
from app.models.user import UserCreate, UserUpdate, UserRole


async def get_user_collection(db: AsyncIOMotorDatabase):
    """Получение коллекции пользователей."""
    return db.users


async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> Optional[Dict[str, Any]]:
    """Получение пользователя по ID."""
    try:
        collection = await get_user_collection(db)
        user = await collection.find_one({"_id": ObjectId(user_id)})
        if user:
            user["id"] = str(user["_id"])
            del user["_id"]
            if "password" in user:
                del user["password"]
        return user
    except Exception:
        return None


async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[Dict[str, Any]]:
    """Получение пользователя по email."""
    collection = await get_user_collection(db)
    user = await collection.find_one({"email": email})
    if user:
        user["id"] = str(user["_id"])
        del user["_id"]
    return user


async def get_user_by_username(db: AsyncIOMotorDatabase, username: str) -> Optional[Dict[str, Any]]:
    """Получение пользователя по username."""
    collection = await get_user_collection(db)
    user = await collection.find_one({"username": username})
    if user:
        user["id"] = str(user["_id"])
        del user["_id"]
    return user


async def get_users(
    db: AsyncIOMotorDatabase, 
    skip: int = 0, 
    limit: int = 100, 
    role: Optional[UserRole] = None
) -> List[Dict[str, Any]]:
    """Получение списка пользователей."""
    collection = await get_user_collection(db)
    
    # Построение фильтра
    filter_query = {}
    if role:
        filter_query["role"] = role
    
    cursor = collection.find(filter_query).skip(skip).limit(limit)
    users = []
    
    async for user in cursor:
        user["id"] = str(user["_id"])
        del user["_id"]
        if "password" in user:
            del user["password"]
        users.append(user)
        
    return users


async def create_user(db: AsyncIOMotorDatabase, user_data: UserCreate) -> Dict[str, Any]:
    """Создание нового пользователя."""
    # Проверка наличия пользователя с таким же email
    if await get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Проверка наличия пользователя с таким же username
    if await get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Подготовка данных для вставки
    now = datetime.utcnow()
    user_dict = user_data.model_dump()
    user_dict["password"] = get_password_hash(user_dict["password"])
    user_dict["created_at"] = now
    user_dict["updated_at"] = now
    
    # Вставка в базу данных
    collection = await get_user_collection(db)
    result = await collection.insert_one(user_dict)
    
    # Получение созданного пользователя
    user = await get_user_by_id(db, str(result.inserted_id))
    return user


async def update_user(
    db: AsyncIOMotorDatabase, 
    user_id: str, 
    user_data: UserUpdate
) -> Optional[Dict[str, Any]]:
    """Обновление данных пользователя."""
    # Проверка существования пользователя
    existing_user = await get_user_by_id(db, user_id)
    if not existing_user:
        return None
    
    # Подготовка данных для обновления (исключаем None значения)
    update_data = {k: v for k, v in user_data.model_dump(exclude_unset=True).items() if v is not None}
    
    # Проверка уникальности email, если он изменяется
    if "email" in update_data and update_data["email"] != existing_user.get("email"):
        if await get_user_by_email(db, update_data["email"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Проверка уникальности username, если он изменяется
    if "username" in update_data and update_data["username"] != existing_user.get("username"):
        if await get_user_by_username(db, update_data["username"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Добавляем время обновления
    update_data["updated_at"] = datetime.utcnow()
    
    # Выполнение обновления
    collection = await get_user_collection(db)
    await collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    # Возвращаем обновленного пользователя
    return await get_user_by_id(db, user_id)


async def delete_user(db: AsyncIOMotorDatabase, user_id: str) -> bool:
    """Удаление пользователя."""
    try:
        collection = await get_user_collection(db)
        result = await collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0
    except Exception:
        return False


async def authenticate_user(
    db: AsyncIOMotorDatabase, 
    username_or_email: str, 
    password: str
) -> Optional[Dict[str, Any]]:
    """Аутентификация пользователя по имени пользователя/email и паролю."""
    # Проверка, является ли входная строка email
    is_email = "@" in username_or_email
    
    # Поиск пользователя
    if is_email:
        user = await get_user_by_email(db, username_or_email)
    else:
        user = await get_user_by_username(db, username_or_email)
    
    if not user:
        return None
    
    # Проверка пароля
    if not verify_password(password, user.get("password", "")):
        return None
    
    # Удаление пароля из возвращаемых данных
    if "password" in user:
        del user["password"]
    
    return user


async def change_user_password(
    db: AsyncIOMotorDatabase, 
    user_id: str, 
    current_password: str, 
    new_password: str
) -> bool:
    """Изменение пароля пользователя."""
    # Получение пользователя с паролем
    collection = await get_user_collection(db)
    user = await collection.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        return False
    
    # Проверка текущего пароля
    if not verify_password(current_password, user.get("password", "")):
        return False
    
    # Хеширование нового пароля
    hashed_password = get_password_hash(new_password)
    
    # Обновление пароля
    await collection.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "password": hashed_password,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return True 