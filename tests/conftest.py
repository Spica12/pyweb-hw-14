import asyncio

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from main import app, startup
from src.dependencies.database import get_db
from src.models.base import Base
from src.models.users import UserModel
from src.services.auth import auth_service

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)

test_user = {"username": "test_user@example.com", "password": "qaz12EDC"}


@pytest.fixture(scope="module", autouse=True)
def init_models_wrap():

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        async with TestingSessionLocal() as session:
            hash_password = auth_service.get_password_hash(test_user["password"])
            current_user = UserModel(
                username=test_user["username"], password=hash_password, confirmed=True
            )
            session.add(current_user)
            await session.commit()

    asyncio.run(init_models())


@pytest.fixture(scope="module")
def client():

    async def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        except Exception as err:
            print(err)
            await session.rollback()
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)


@pytest_asyncio.fixture()
async def get_token():
    token = await auth_service.create_access_token(data={"sub": test_user["username"]})

    return token
