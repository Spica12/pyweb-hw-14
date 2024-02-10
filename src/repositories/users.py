from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.database import get_db
from src.models.users import TokenModel, UserModel
from src.schemas.user import UserCreateSchema, UserResetPasswordSchema


class UserRepo:
    def __init__(self, db):
        """
        The __init__ function is called when the class is instantiated.
        It sets up the database connection and creates a new session for each request.

        :param self: Represent the instance of the class
        :param db: Pass in a database connection to the class
        :return: Nothing
        """
        self.db: AsyncSession = db

    async def get_user_by_username(self, username: str):
        """
        The get_user_by_username function is used to retrieve a user from the database by their username.


        :param self: Represent the instance of the class
        :param username: str: Filter the user by username
        :return: A user object
        """
        stmt = select(UserModel).filter_by(username=username)
        user = await self.db.execute(stmt)
        user = user.scalar_one_or_none()

        return user

    async def create_user(self, body: UserCreateSchema):
        """
        The create_user function creates a new user in the database.
            ---
            post:
              description: Create a new user.
              requestBody:
                content:
                  application/json:
                    schema: UserCreateSchema

        :param self: Represent the instance of a class
        :param body: UserCreateSchema: Validate the data that is being passed in
        :return: A new user object
        """
        new_user = UserModel(
            **body.model_dump(), avatar=f"http://127.0.0.1:8000/api/users/default_avatar"
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        return new_user

    async def update_token(self, user: UserModel, refresh_token: str | None):
        """
        The update_token function updates the refresh token for a user.
            If the user does not have a refresh token, it creates one.


        :param self: Make the function a method of the class
        :param user: UserModel: Get the user id from the usermodel class
        :param refresh_token: str | None: Check if the refresh token is valid or not
        :return: The token that was updated
        """
        stmt = select(TokenModel).filter_by(user_id=user.id)
        token = await self.db.execute(stmt)
        token = token.scalar_one_or_none()
        if token:
            token.refresh_token = refresh_token
        else:
            new_token = TokenModel(refresh_token=refresh_token, user_id=user.id)
            self.db.add(new_token)
        await self.db.commit()

    async def get_refresh_token(self, user: UserModel):
        """
        The get_refresh_token function is used to retrieve the refresh token for a given user.


        :param self: Represent the instance of a class
        :param user: UserModel: Get the user id from the usermodel class
        :return: A refresh token
        """
        stmt = select(TokenModel).filter_by(user_id=user.id)
        token = await self.db.execute(stmt)
        token = token.scalar_one_or_none()

        return token.refresh_token

    async def confirmed_email(self, email: str):
        """
        The confirmed_email function is used to set the confirmed field of a user to True.


        :param self: Represent the instance of the class
        :param email: str: Get the email address of the user
        :return: Nothing
        """
        user = await self.get_user_by_username(email)
        user.confirmed = True
        await self.db.commit()

    async def update_avatar_url(self, username: str, url: str | None):
        """
        The update_avatar_url function updates the avatar url of a user.

        :param self: Represent the instance of the class
        :param username: str: Get the user by their username
        :param url: str | None: Check if the url is a string or none
        :return: The user object
        """
        user = await self.get_user_by_username(username)

        user.avatar = url
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def change_password(self, body: UserResetPasswordSchema):
        """
        The change_password function changes the password of a user.
                Args:
                    body (UserResetPasswordSchema): The new password for the user.

        :param self: Represent the instance of a class
        :param body: UserResetPasswordSchema: Get the username and password from the request body
        :return: A user object
        """
        user = await self.get_user_by_username(body.username)
        user.password = body.password
        await self.db.commit()
