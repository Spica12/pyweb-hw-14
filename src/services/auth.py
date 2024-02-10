from datetime import datetime, timedelta
import pickle
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
import redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import config
from src.dependencies.database import get_db
from src.models.users import UserModel
from src.repositories.users import UserRepo
from src.schemas.user import UserCreateSchema, UserResetPasswordSchema


class AuthService:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = config.SECRET_KEY_JWT
    ALGORITHM = config.ALGORITHM
    cache = redis.Redis(
        host=config.REDIS_DOMAIN,
        port=config.REDIS_PORT,
        db=0,
        password=config.REDIS_PASSWORD,
    )

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

    # def __init__(self, db: AsyncSession):
    #     self.repo = UserRepo(db=db)

    def get_password_hash(self, password: str):
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password, hashed_pasword):
        return self.pwd_context.verify(plain_password, hashed_pasword)

    async def create_user(self, body: UserCreateSchema, db: AsyncSession):
        new_user = await UserRepo(db).create_user(body)
        return new_user

    async def get_user_by_username(self, username: str, db: AsyncSession):
        user = await UserRepo(db).get_user_by_username(username)
        return user

    async def create_access_token(
        self, data: dict, expires_delta: Optional[float] = None
    ):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"}
        )
        encode_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

        return encode_jwt

    async def create_refresh_token(
        self, data: dict, expires_delta: Optional[float] = None
    ):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"}
        )
        encode_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

        return encode_jwt

    async def update_refresh_token(
        self, user: UserModel, refresh_token: str | None, db: AsyncSession
    ):
        await UserRepo(db).update_token(user, refresh_token)

    async def decode_refresh_token(self, refresh_token: str):
        try:
            payload = jwt.decode(
                refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM]
            )
            if payload["scope"] == "refresh_token":
                username = payload["sub"]
                return username
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid scope for token",
            )

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    async def get_refresh_token_by_user(self, user: UserModel, db: AsyncSession):
        refresh_token = await UserRepo(db).get_refresh_token(user)
        return refresh_token

    async def get_current_user(
        self, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
    ):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-AUTHENTICATE": "BEARER"},
        )
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            username = payload["sub"]
            if payload["scope"] == "access_token":
                if username is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user_hash = str(username)
        user = self.cache.get(user_hash)
        if user is None:
            print("user from DB")
            user = await UserRepo(db).get_user_by_username(username)
            if user is None:
                raise credentials_exception
            self.cache.set(user_hash, pickle.dumps(user))
            self.cache.expire(user_hash, time=300)
        else:
            print("user from cache")
            user = pickle.loads(user)

        return user

    async def create_email_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

        return token

    async def get_email_from_token(self, token: str):
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email

        except JWTError as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid token for email verification",
            )

    async def confirmed_email(
        self, email: str, db: AsyncSession = Depends(get_db)
    ) -> None:
        await UserRepo(db).confirmed_email(email)

    async def change_password(self, body: UserResetPasswordSchema, db: AsyncSession):
        await UserRepo(db).change_password(body)


auth_service = AuthService()
