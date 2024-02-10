from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.users import UserRepo


class UserService:

    def __init__(self, db: AsyncSession):
        self.repo = UserRepo(db=db)

    async def update_avatar(self, email: str, url: str):
        user = await self.repo.update_avatar_url(email, url)

        return user
