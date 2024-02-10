from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.users import UserRepo


class UserService:

    def __init__(self, db: AsyncSession):
        """
        The __init__ function is called when the class is instantiated.
        It sets up the UserRepo object, which will be used to interact with the database.

        :param self: Represent the instance of the class
        :param db: AsyncSession: Create a connection to the database
        :return: Nothing
        """
        self.repo = UserRepo(db=db)

    async def update_avatar(self, email: str, url: str):
        """
        The update_avatar function updates the avatar url of a user.

        Args:
            email (str): The email address of the user to update.
            url (str): The new avatar URL for the user.

        :param self: Represent the instance of the class
        :param email: str: Identify the user
        :param url: str: Update the avatar url of a user
        :return: A user object
        """
        user = await self.repo.update_avatar_url(email, url)

        return user
