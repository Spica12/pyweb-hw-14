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
        """
        The get_password_hash function takes a password as input and returns the hash of that password.
            The function uses the pwd_context object to generate a hash from the given password.

        :param self: Represent the instance of the class
        :param password: str: Pass the password that is being hashed
        :return: A hash of the password
        """
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password, hashed_pasword):
        """
        The verify_password function takes a plain-text password and the hashed version of that password,
        and returns True if they match, False otherwise. This is used to verify that the user's login attempt
        is valid.

        :param self: Represent the instance of the class
        :param plain_password: Store the password that is being verified
        :param hashed_pasword: Compare the plain_password parameter to see if they match
        :return: A boolean value, true or false
        """
        return self.pwd_context.verify(plain_password, hashed_pasword)

    async def create_user(self, body: UserCreateSchema, db: AsyncSession):
        """
        The create_user function creates a new user in the database.
            Args:
                body (UserCreateSchema): The schema for creating a new user.
                db (AsyncSession): The database session to use for this request.
            Returns:
                UserModel: A model of the newly created user.

        :param self: Represent the instance of the class
        :param body: UserCreateSchema: Validate the data that is passed in
        :param db: AsyncSession: Create a database connection
        :return: A user object
        """
        new_user = await UserRepo(db).create_user(body)
        return new_user

    async def get_user_by_username(self, username: str, db: AsyncSession):
        """
        The get_user_by_username function is used to get a user by their username.
            Args:
                username (str): The username of the user you want to retrieve.
                db (AsyncSession): An async database session object that will be used for querying the database.

        :param self: Represent the instance of the class
        :param username: str: Get the username from the user
        :param db: AsyncSession: Pass in the database session
        :return: A user object
        """
        user = await UserRepo(db).get_user_by_username(username)
        return user

    async def create_access_token(
        self, data: dict, expires_delta: Optional[float] = None
    ):
        """
        The create_access_token function creates a new access token for the user.
            Args:
                data (dict): A dictionary containing all the information to be encoded in the JWT.
                expires_delta (Optional[float]): An optional parameter that specifies how long until
                    this token expires, in seconds. If not specified, it defaults to 7 days from now.

        :param self: Represent the instance of the class
        :param data: dict: Store the data that you want to encode
        :param expires_delta: Optional[float]: Set the expiration time of the token
        :return: A token, but i don't know how to use it
        """
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
        """
        The create_refresh_token function creates a refresh token for the user.
            Args:
                data (dict): The data to be encoded in the JWT.
                expires_delta (Optional[float]): The time until expiration of the JWT, defaults to 15 minutes if not specified.

        :param self: Represent the instance of the class
        :param data: dict: Store the user's id and username
        :param expires_delta: Optional[float]: Set the expiration time for the token
        :return: A jwt token
        """
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
        """
        The update_refresh_token function updates the refresh token for a user.
            Args:
                self (UserService): The UserService object.
                user (UserModel): The UserModel object to update the refresh token for.
                refresh_token (str | None): The new value of the refresh token, or None if it should be deleted from storage.

        :param self: Denote that the function is a method of the class
        :param user: UserModel: Identify the user that is being updated
        :param refresh_token: str | None: Update the refresh token in the database
        :param db: AsyncSession: Pass the database session to the userrepo class
        :return: The usermodel object
        """
        await UserRepo(db).update_token(user, refresh_token)

    async def decode_refresh_token(self, refresh_token: str):
        """
        The decode_refresh_token function takes a refresh token and decodes it.
        If the scope is not &quot;refresh_token&quot;, then an error is raised. If the JWTError exception occurs,
        then another error is raised.

        :param self: Represent the instance of the class
        :param refresh_token: str: Pass the refresh token to the function
        :return: The username of the user who made the request
        """
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
        """
        The get_refresh_token_by_user function is used to get the refresh token for a user.

        Args:
            user (UserModel): The UserModel object that contains the information about the user.
            db (AsyncSession): The database session that will be used to query for data.

        Returns:  A string containing the refresh token of a given user.

        :param self: Represent the instance of a class
        :param user: UserModel: Get the user_id from the usermodel object
        :param db: AsyncSession: Pass in the database session
        :return: The refresh token of the user
        """
        refresh_token = await UserRepo(db).get_refresh_token(user)
        return refresh_token

    async def get_current_user(
        self, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
    ):
        """
        The get_current_user function is a dependency that will be used in the
            protected endpoints. It takes a token and returns the user object if it's valid,
            otherwise raises an HTTPException with status code 401 (Unauthorized).

        :param self: Denote that the function is a method of the class
        :param token: str: Get the token from the request header
        :param db: AsyncSession: Get the database session
        :return: The user object
        """
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
        """
        The create_email_token function creates a JWT token that is used to verify the user's email address.
            The token contains the following data:
                - iat (issued at): The time when the token was created.
                - exp (expiration): When this token expires, 7 days from now.

        :param self: Represent the instance of the class
        :param data: dict: Pass the data that will be encoded into the token
        :return: A token that is encoded with the information in the data dictionary
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

        return token

    async def get_email_from_token(self, token: str):
        """
        The get_email_from_token function takes a token as an argument and returns the email address associated with that token.
        If the token is invalid, it raises an HTTPException.

        :param self: Represent the instance of a class
        :param token: str: Pass in the token that is being decoded
        :return: The email address that was used to create the token
        """
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
        """
        The confirmed_email function is used to confirm a user's email address.
            Args:
                email (str): The user's email address.
                db (AsyncSession): An async database session object.

        :param self: Represent the instance of the class
        :param email: str: Pass the email to the function
        :param db: AsyncSession: Pass the database session to the userrepo class
        :return: None
        """
        await UserRepo(db).confirmed_email(email)

    async def change_password(self, body: UserResetPasswordSchema, db: AsyncSession):
        """
        The change_password function is used to change the password of a user.
                Args:
                    body (UserResetPasswordSchema): The schema for changing a user's password.

        :param self: Represent the instance of a class
        :param body: UserResetPasswordSchema: Validate the request body
        :param db: AsyncSession: Pass the database session to the userrepo class
        :return: Nothing
        """
        await UserRepo(db).change_password(body)


auth_service = AuthService()
