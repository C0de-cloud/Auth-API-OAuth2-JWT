from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status, Body
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_database, get_current_user, get_current_admin_user
from app.crud.user import get_user_by_id, get_users, update_user, delete_user
from app.models.user import User, UserUpdate, UserRole

router = APIRouter()


@router.get("/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Получение информации о текущем пользователе."""
    return current_user


@router.put("/me", response_model=User)
async def update_user_me(
    user_data: Annotated[UserUpdate, Body(...)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
):
    """Обновление информации о текущем пользователе."""
    # Убеждаемся, что пользователь не может сам себе изменить роль
    if hasattr(user_data, "role") and user_data.role is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to change your own role"
        )
    
    updated_user = await update_user(db, current_user["id"], user_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not update user"
        )
    return updated_user


@router.get("", response_model=List[User])
async def read_users(
    skip: Annotated[int, Query(0, ge=0)] = 0,
    limit: Annotated[int, Query(100, ge=1, le=100)] = 100,
    role: Annotated[Optional[UserRole], Query(None)] = None,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
):
    """
    Получение списка пользователей.
    Только для администраторов.
    """
    return await get_users(db, skip, limit, role)


@router.get("/{user_id}", response_model=User)
async def read_user(
    user_id: Annotated[str, Path(...)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
):
    """
    Получение информации о пользователе по ID.
    Пользователи могут получать только собственную информацию.
    Администраторы могут получать информацию о любом пользователе.
    """
    # Проверка прав доступа
    if current_user["id"] != user_id and current_user.get("role") != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return user


@router.put("/{user_id}", response_model=User)
async def update_user_admin(
    user_id: Annotated[str, Path(...)],
    user_data: Annotated[UserUpdate, Body(...)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
):
    """
    Обновление информации о пользователе.
    Только для администраторов.
    """
    updated_user = await update_user(db, user_id, user_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_admin(
    user_id: Annotated[str, Path(...)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
):
    """
    Удаление пользователя.
    Только для администраторов.
    """
    # Проверяем, не пытается ли админ удалить самого себя
    if current_user["id"] == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    success = await delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return None 