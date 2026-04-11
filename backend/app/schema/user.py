from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime


class RegisterRequest(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not v.strip():
            raise ValueError("Username cannot be empty")
        if " " in v:
            raise ValueError("Username cannot contain spaces")
        if len(v) < 3 or len(v) > 15:
            raise ValueError("Username must be between 3 and 15 characters")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return v


class LoginRequest(BaseModel):
    identifier: str  
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None