from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role: UserRole = Field(default=UserRole.USER)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    id: str
    role: UserRole
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True, 
        populate_by_name=True
    )


class User(UserInDB):
    """Модель пользователя без чувствительных данных"""
    pass


class Token(BaseModel):
    """Модель JWT токена"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Данные, хранящиеся в JWT токене"""
    user_id: str
    username: str
    email: str
    role: UserRole
    expires: datetime 