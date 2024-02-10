import uuid
from datetime import date

from pydantic import BaseModel, EmailStr, Field


class UserCreateSchema(BaseModel):
    username: EmailStr
    password: str = Field(min_length=6, max_length=12)


class UserReadSchema(BaseModel):
    id: uuid.UUID
    username: EmailStr
    password: str
    avatar: str | None


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'


class UserResetPasswordSchema(BaseModel):
    username: EmailStr
    password: str = Field(min_length=6, max_length=12)
    confirm_password: str = Field(min_length=6, max_length=12)
