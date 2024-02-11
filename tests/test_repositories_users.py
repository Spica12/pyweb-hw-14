import unittest
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.users import TokenModel, UserModel
from src.repositories.users import UserRepo
from src.schemas.user import UserCreateSchema, UserResetPasswordSchema


class TestAsyncUser(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.user_confirmed = UserModel(
            id=1,
            username="user_confirmed@example.com",
            password="string564123",
            confirmed=True,
            avatar=None,
        )
        self.user_not_confirmed = UserModel(
            id=1,
            username="user_not_confirmed@example.com",
            password="string564123",
            confirmed=False,
            avatar=None,
        )
        self.session = AsyncMock(spec=AsyncSession)
        self.repo = UserRepo(self.session)

    async def test_get_user_by_username_found(self):
        username = "user_confirmed"
        mocked_user = MagicMock()
        mocked_user.scalar_one_or_none.return_value = self.user_confirmed
        self.session.execute.return_value = mocked_user

        result = await self.repo.get_user_by_username(username)

        self.assertIsInstance(result, UserModel)
        self.assertEqual(result.username, self.user_confirmed.username)
        self.assertEqual(result.password, self.user_confirmed.password)
        self.assertEqual(result.confirmed, self.user_confirmed.confirmed)
        self.assertEqual(result.avatar, self.user_confirmed.avatar)

    async def test_get_user_by_username_not_found(self):
        username = "user_confirmed"
        mocked_user = MagicMock()
        mocked_user.scalar_one_or_none.return_value = None
        self.session.execute.return_value = mocked_user

        result = await self.repo.get_user_by_username(username)

        self.assertIsNone(result)

    async def test_create_user(self):
        body = UserCreateSchema(
            username="test_create_user@example.com",
            password="qaz123wsx",
        )

        result = await self.repo.create_user(body)

        self.assertIsInstance(result, UserModel)
        self.assertEqual(result.username, body.username)
        self.assertEqual(result.password, body.password)
        self.assertFalse(result.confirmed)
        self.assertEqual(
            result.avatar, f"http://127.0.0.1:8000/api/users/default_avatar"
        )

    async def test_update_token_found(self):
        refresh_token = TokenModel()
        mocked_token = MagicMock()
        mocked_token.scalar_one_or_none.return_value = TokenModel()
        self.session.execute.return_value = mocked_token

        result = await self.repo.update_token(
            user=self.user_confirmed, refresh_token=refresh_token
        )

        self.session.add.assert_not_called()
        self.session.commit.assert_called_once()
        self.assertIsNone(result)

    async def test_update_token_not_found(self):
        refresh_token = TokenModel()
        mocked_token = MagicMock()
        mocked_token.scalar_one_or_none.return_value = None
        self.session.execute.return_value = mocked_token

        result = await self.repo.update_token(
            user=self.user_confirmed, refresh_token=refresh_token
        )

        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()
        self.assertIsNone(result)

    async def test_get_refresh_token_found(self):
        refresh_token = TokenModel(refresh_token="abcd")
        mocked_token = MagicMock()
        mocked_token.scalar_one_or_none.return_value = refresh_token
        self.session.execute.return_value = mocked_token

        result = await self.repo.get_refresh_token(user=self.user_confirmed)

        self.assertIsInstance(result, str)
        self.assertEqual(result, refresh_token.refresh_token)

    async def test_confirmed_email(self):
        email = "email@example.com"
        user = self.user_not_confirmed

        mocked_user_repo = UserRepo(self.session)
        mocked_user_repo.get_user_by_username = AsyncMock(return_value=user)

        await mocked_user_repo.confirmed_email(email)

        mocked_user_repo.get_user_by_username.assert_called_once_with(email)
        self.assertTrue(user.confirmed)

    async def test_update_avatar_url(self):
        url = "http://example.com"
        username = "email@example.com"
        user = self.user_confirmed

        mocked_user_repo = UserRepo(self.session)
        mocked_user_repo.get_user_by_username = AsyncMock(return_value=user)

        result = await mocked_user_repo.update_avatar_url(username, url)

        self.assertIsInstance(result, UserModel)
        self.assertEqual(result.username, user.username)
        self.assertEqual(result.password, user.password)
        self.assertEqual(result.confirmed, user.confirmed)
        self.assertEqual(result.avatar, url)

    async def change_password(self):
        body = UserResetPasswordSchema(
            username="email@example.com",
            password="qwerty12345",
            confirm_password="qwerty12345",
        )
        user = self.user_confirmed

        mocked_user_repo = UserRepo(self.session)
        mocked_user_repo.get_user_by_username = AsyncMock(return_value=user)

        result = await mocked_user_repo.change_password(body)

        self.assertIsNone(result)
        self.assertEqual(user.password, body.password)
        mocked_user_repo.get_user_by_username.assert_called_once_with(body.username)
        self.session.commit.assert_called_once()
