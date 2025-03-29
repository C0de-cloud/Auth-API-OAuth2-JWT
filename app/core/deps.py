from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase
from jose import JWTError

from app.core.security import decode_token
from app.crud.user import get_user_by_id
from app.models.user import User, UserRole, TokenData

# Определение OAuth2 схемы с путем для получения токена
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_database() -> AsyncIOMotorDatabase:
    """Получение экземпляра базы данных."""
    from main import app
    return app.mongodb


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
) -> User:
    """Получение текущего аутентифицированного пользователя"""
    try:
        token_data = decode_token(token)
        user = await get_user_by_id(db, token_data.user_id)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        if not user.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return user
        
    except (JWTError, HTTPException) as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Проверка, что пользователь активен"""
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Проверка, что пользователь имеет права администратора"""
    if current_user.get("role") != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def optional_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Optional[User]:
    """Опциональная проверка пользователя (может использоваться для публичных эндпоинтов,
    но с дополнительной функциональностью для аутентифицированных пользователей)"""
    try:
        return get_current_user(token, db)
    except HTTPException:
        return None 